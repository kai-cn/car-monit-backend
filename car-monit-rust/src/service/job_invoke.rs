// 来源: ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/JobInvokeUtil.java
//       ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/*.java
// 职责: `invoke_target` 字符串的解析（bean/方法/参数）与实际执行，替代 Java 反射。
// 对应关系: JobInvokeUtil.invokeMethod -> invoke；SpringUtils.getBean / Class.forName -> BEANS 查表。
//
// 解析规则按 Java 逐条照搬，包含它的朴素切分与类型猜测：`ryParams('a,b')` 会切成两个 String
// 参数从而抛 NoSuchMethodException，`TRUE` 不会被当成布尔（equals 是大小写敏感的）。
// 异常只对齐**首行**（`类全名: message`），后续 Java 栈帧无法在 Rust 侧复刻。

use crate::state::AppState;
use crate::task;

/// Java: 一个可被 sys_job 调用的 bean：名字、类全名、方法签名。
pub struct Bean {
    pub name: &'static str,
    pub class: &'static str,
    /// Java 侧是否为每个字段都注入了依赖；`Class.forName(...).newInstance()`
    /// 出来的新实例没有依赖，调用即 NPE。
    pub requires_injection: bool,
    pub methods: &'static [Method],
}

pub struct Method {
    pub name: &'static str,
    /// 形参类型全名，用于 `getDeclaredMethod` 的精确匹配与异常文案。
    pub params: &'static [&'static str],
}

const STRING: &str = "java.lang.String";
const BOOLEAN: &str = "java.lang.Boolean";
const LONG: &str = "java.lang.Long";
const DOUBLE: &str = "java.lang.Double";
const INTEGER: &str = "java.lang.Integer";

/// Java: Spring 容器里的任务 bean。`ryTask` 无依赖，其余都靠 @Autowired。
static BEANS: &[Bean] = &[
    Bean {
        name: "ryTask",
        class: "com.ruoyi.quartz.task.RyTask",
        requires_injection: false,
        methods: &[
            Method {
                name: "ryNoParams",
                params: &[],
            },
            Method {
                name: "ryParams",
                params: &[STRING],
            },
            Method {
                name: "ryMultipleParams",
                params: &[STRING, BOOLEAN, LONG, DOUBLE, INTEGER],
            },
            Method {
                name: "autoBuildGoodsHb",
                params: &[],
            },
        ],
    },
    Bean {
        name: "vehicleMonitoringTask",
        class: "com.ruoyi.quartz.task.VehicleMonitoringTask",
        requires_injection: true,
        methods: &[
            Method {
                name: "syncOrgInfo",
                params: &[],
            },
            Method {
                name: "syncSectionInfo",
                params: &[],
            },
            Method {
                name: "syncGantryInfo",
                params: &[],
            },
            Method {
                name: "syncServiceAreaInfoInfo",
                params: &[],
            },
            Method {
                name: "syncTollBoothInfoInfo",
                params: &[],
            },
            Method {
                name: "syncSfzjcxxInfoInfo",
                params: &[],
            },
            Method {
                name: "syncTollStationInfo",
                params: &[],
            },
        ],
    },
    Bean {
        name: "orgTask",
        class: "com.ruoyi.quartz.task.OrgTask",
        requires_injection: true,
        methods: &[Method {
            name: "syncOrgInfo",
            params: &[],
        }],
    },
    Bean {
        name: "trackTask",
        class: "com.ruoyi.quartz.task.TrackTask",
        requires_injection: true,
        methods: &[
            Method {
                name: "syncCurrentTrack",
                params: &[],
            },
            Method {
                name: "syncSuspiciousCar",
                params: &[],
            },
            Method {
                name: "syncHistoryTrack",
                params: &[],
            },
            Method {
                name: "saveCarExcept",
                params: &[],
            },
            Method {
                name: "syncHistoryTrackNoCar",
                params: &[],
            },
            Method {
                name: "changeCarSuspicious",
                params: &[],
            },
        ],
    },
    Bean {
        name: "partitionMaintenanceTask",
        class: "com.ruoyi.quartz.task.PartitionMaintenanceTask",
        requires_injection: true,
        methods: &[
            Method {
                name: "createFuturePartitions",
                params: &[],
            },
            Method {
                name: "checkPartitionHealth",
                params: &[],
            },
        ],
    },
    Bean {
        name: "snapshotFlowSyncTask",
        class: "com.ruoyi.quartz.task.SnapshotFlowSyncTask",
        requires_injection: true,
        methods: &[
            Method {
                name: "init",
                params: &[],
            },
            Method {
                name: "syncFullData",
                params: &[],
            },
            Method {
                name: "syncSingleMonth",
                // Java: (String, AtomicInteger) —— AtomicInteger 永远匹配不上，照抄。
                params: &[STRING, "java.util.concurrent.atomic.AtomicInteger"],
            },
            Method {
                name: "syncIncrementalData",
                params: &[],
            },
            Method {
                name: "manualFullSync",
                params: &[],
            },
            Method {
                name: "manualIncrementalSync",
                params: &[],
            },
            Method {
                name: "preCreateTables",
                params: &["int"],
            },
        ],
    },
    Bean {
        name: "shardingTableTask",
        class: "com.ruoyi.base.task.ShardingTableTask",
        requires_injection: true,
        methods: &[
            Method {
                name: "createShardingTables",
                params: &[],
            },
            Method {
                name: "manualCreateTables",
                params: &["int"],
            },
        ],
    },
    Bean {
        name: "viewMaintenanceTask",
        class: "com.ruoyi.base.task.ViewMaintenanceTask",
        requires_injection: true,
        methods: &[
            Method {
                name: "scheduledViewMaintenance",
                params: &[],
            },
            Method {
                name: "manualTrigger",
                params: &[],
            },
            Method {
                name: "getMetrics",
                params: &[],
            },
            Method {
                name: "needsUpdate",
                params: &[],
            },
            Method {
                name: "getViewDefinition",
                params: &[],
            },
        ],
    },
];

/// Java: `JobInvokeUtil.invokeMethod(sysJob)`。`Err` 里是异常首行文案。
pub async fn invoke(state: &AppState, invoke_target: &str) -> Result<(), String> {
    let bean_name = get_bean_name(invoke_target);
    let method_name = get_method_name(invoke_target);
    let params = get_method_params(invoke_target)?;
    let by_class = is_valid_class_name(&bean_name);
    let bean = if by_class {
        BEANS
            .iter()
            .find(|bean| bean.class == bean_name)
            .ok_or_else(|| format!("java.lang.ClassNotFoundException: {bean_name}"))?
    } else {
        BEANS
            .iter()
            .find(|bean| bean.name == bean_name)
            .ok_or_else(|| {
                format!(
                    "org.springframework.beans.factory.NoSuchBeanDefinitionException: No bean named '{bean_name}' available"
                )
            })?
    };
    let param_types: Vec<&str> = params.iter().map(|param| param.fqn()).collect();
    let types = param_types.as_slice();
    let method = bean
        .methods
        .iter()
        .find(|method| method.name == method_name && method.params == types)
        .ok_or_else(|| {
            format!(
                "java.lang.NoSuchMethodException: {}.{}({})",
                bean.class,
                method_name,
                types.join(", ")
            )
        })?;
    // Java: Class.forName(beanName).newInstance() 出来的新实例没有被注入的依赖，
    // 方法体里一解引用就 NPE，而反射会把目标异常包成 InvocationTargetException。
    if by_class && bean.requires_injection {
        return Err("java.lang.reflect.InvocationTargetException".to_string());
    }
    execute(state, bean.name, method.name, &params).await
}

/// JobInvokeUtil 只产出这四种装箱类型。
#[derive(Debug, Clone)]
enum JavaParam {
    Str(String),
    Bool(bool),
    Long(i64),
    Double(f64),
    Int(i32),
}

impl JavaParam {
    fn fqn(&self) -> &'static str {
        match self {
            JavaParam::Str(_) => STRING,
            JavaParam::Bool(_) => BOOLEAN,
            JavaParam::Long(_) => LONG,
            JavaParam::Double(_) => DOUBLE,
            JavaParam::Int(_) => INTEGER,
        }
    }

    /// Java: `System.out.println` 里各类型的字符串形式。
    fn display(&self) -> String {
        match self {
            JavaParam::Str(text) => text.clone(),
            JavaParam::Bool(value) => value.to_string(),
            JavaParam::Long(value) => value.to_string(),
            JavaParam::Double(value) => format_double(*value),
            JavaParam::Int(value) => value.to_string(),
        }
    }
}

/// Java: `Double.toString` 整数值带 `.0` 后缀。
fn format_double(value: f64) -> String {
    let text = value.to_string();
    if !text.contains('.')
        && !text.contains('e')
        && !text.contains("NaN")
        && !text.contains("Infinity")
    {
        return format!("{text}.0");
    }
    text
}

/// Java: `isValidClassName` —— 数的是 beanName 里点的个数 > 1。
fn is_valid_class_name(name: &str) -> bool {
    count_matches(name, '.') > 1
}

fn count_matches(text: &str, token: char) -> usize {
    text.chars().filter(|c| *c == token).count()
}

/// Java: `getBeanName` —— substringBefore("(") 再 substringBeforeLast(".")。
fn get_bean_name(target: &str) -> String {
    before_last(&before(target, '('), '.')
}

/// Java: `getMethodName` —— substringBefore("(") 再 substringAfterLast(".")。
fn get_method_name(target: &str) -> String {
    after_last(&before(target, '('), '.')
}

/// Java: `StringUtils.substringBefore(str, sep)`，sep 不存在时返回原串。
fn before(text: &str, token: char) -> String {
    match text.find(token) {
        Some(index) => text[..index].to_string(),
        None => text.to_string(),
    }
}

/// Java: `StringUtils.substringBeforeLast(str, sep)`，找不到就原样返回。
fn before_last(text: &str, token: char) -> String {
    match text.rfind(token) {
        Some(index) if !text.is_empty() => text[..index].to_string(),
        _ => text.to_string(),
    }
}

/// Java: `StringUtils.substringAfterLast(str, sep)`，找不到返回 ""。
fn after_last(text: &str, token: char) -> String {
    match text.rfind(token) {
        Some(index) if !text.is_empty() => text[index + token.len_utf8()..].to_string(),
        _ => String::new(),
    }
}

/// Java: `StringUtils.substringBetween(str, "(", ")")`，缺任一个返回 null。
fn substring_between(text: &str, open: char, close: char) -> Option<String> {
    let start = text.find(open)? + open.len_utf8();
    let end = start + text[start..].find(close)?;
    Some(text[start..end].to_string())
}

/// Java: `getMethodParams`。`None` 表示无参；`Err` 是 NumberFormatException 首行。
fn get_method_params(target: &str) -> Result<Vec<JavaParam>, String> {
    let inner = substring_between(target, '(', ')');
    let inner = inner.filter(|text| !text.is_empty());
    let Some(inner) = inner else {
        return Ok(Vec::new());
    };
    let mut params = Vec::new();
    for raw in java_split(&inner, ',') {
        let str_value = raw.trim().to_string();
        if str_value.contains('\'') {
            params.push(JavaParam::Str(str_value.replace('\'', "")));
        } else if str_value == "true" || str_value.eq_ignore_ascii_case("false") {
            params.push(JavaParam::Bool(str_value == "true"));
        } else if str_value.to_lowercase().contains('l') {
            let digits = remove_ignore_case(&str_value, 'l');
            params.push(JavaParam::Long(parse_long(&digits, &str_value)?));
        } else if str_value.to_lowercase().contains('d') {
            let digits = remove_ignore_case(&str_value, 'd');
            params.push(JavaParam::Double(parse_double(&digits, &str_value)?));
        } else {
            params.push(JavaParam::Int(parse_int(&str_value)?));
        }
    }
    Ok(params)
}

/// Java: `String.split(",")`——去掉尾部空串。
fn java_split(text: &str, token: char) -> Vec<String> {
    let mut parts: Vec<String> = text.split(token).map(str::to_string).collect();
    while parts.last().map(String::is_empty).unwrap_or(false) {
        parts.pop();
    }
    parts
}

fn remove_ignore_case(text: &str, token: char) -> String {
    text.chars()
        .filter(|c| *c != token && c.to_ascii_lowercase() != token)
        .collect()
}

/// Java: `NumberFormatException: For input string: "xxx"`，xxx 是**处理前**的原始串。
fn number_format_error(text: &str) -> String {
    format!("java.lang.NumberFormatException: For input string: \"{text}\"")
}

fn parse_int(text: &str) -> Result<i32, String> {
    text.parse::<i32>().map_err(|_| number_format_error(text))
}

fn parse_long(digits: &str, original: &str) -> Result<i64, String> {
    digits
        .parse::<i64>()
        .map_err(|_| number_format_error(original))
}

fn parse_double(digits: &str, original: &str) -> Result<f64, String> {
    match digits.to_ascii_lowercase().as_str() {
        "nan" => return Ok(f64::NAN),
        "infinity" => return Ok(f64::INFINITY),
        "-infinity" => return Ok(f64::NEG_INFINITY),
        _ => {}
    }
    digits
        .parse::<f64>()
        .map_err(|_| number_format_error(original))
}

/// Java: `AbstractQuartzJob.doExecute` -> 具体任务方法。
async fn execute(
    state: &AppState,
    bean: &str,
    method: &str,
    params: &[JavaParam],
) -> Result<(), String> {
    let state = state.clone();
    fn log_count(label: &str, result: Result<usize, crate::error::AppError>) {
        match result {
            Ok(count) => tracing::info!("[定时任务] {label}同步完成，共 {count} 条"),
            Err(err) => tracing::error!("[定时任务] {label}同步失败: {err}"),
        }
    }
    match (bean, method) {
        // Java: RyTask 的方法体只往 stdout 打一行日志，无副作用。
        ("ryTask", method) => {
            let values = params
                .iter()
                .map(JavaParam::display)
                .collect::<Vec<_>>()
                .join(", ");
            tracing::info!("[定时任务] 执行演示任务 {method}：{values}");
        }
        ("partitionMaintenanceTask", "createFuturePartitions") => {
            task::run_partition_create(&state).await
        }
        ("partitionMaintenanceTask", "checkPartitionHealth") => {
            task::run_partition_health(&state).await
        }
        ("snapshotFlowSyncTask", "syncIncrementalData") => task::run_incremental_sync(&state).await,
        ("snapshotFlowSyncTask", "manualFullSync") => task::run_full_sync(&state).await,
        ("shardingTableTask", "createShardingTables") => task::run_sharding_tables(&state).await,
        ("viewMaintenanceTask", "scheduledViewMaintenance") => {
            task::run_view_maintenance(&state).await
        }
        ("vehicleMonitoringTask", "syncOrgInfo") => log_count(
            "机构信息",
            crate::task::manager_sync::sync_org(&state).await,
        ),
        ("vehicleMonitoringTask", "syncSectionInfo") => log_count(
            "路段信息",
            crate::task::manager_sync::sync_section(&state).await,
        ),
        ("vehicleMonitoringTask", "syncGantryInfo") => log_count(
            "门架信息",
            crate::task::manager_sync::sync_gantry(&state).await,
        ),
        ("vehicleMonitoringTask", "syncServiceAreaInfoInfo") => log_count(
            "服务区信息",
            crate::task::manager_sync::sync_service_area(&state).await,
        ),
        ("vehicleMonitoringTask", "syncTollBoothInfoInfo") => log_count(
            "收费所信息",
            crate::task::manager_sync::sync_toll_booth(&state).await,
        ),
        ("vehicleMonitoringTask", "syncSfzjcxxInfoInfo") => log_count(
            "收费站基础信息位置",
            crate::task::manager_sync::sync_sfzjcxx(&state).await,
        ),
        ("vehicleMonitoringTask", "syncTollStationInfo") => log_count(
            "收费站信息",
            crate::task::manager_sync::sync_toll_station(&state).await,
        ),
        // Java: OrgTask.syncOrgInfo 方法体全部注释，等价于空操作。
        ("orgTask", "syncOrgInfo") => {
            tracing::info!("[定时任务] orgTask.syncOrgInfo（Java 方法体已注释，跳过）");
        }
        ("trackTask", "syncCurrentTrack") => {
            if let Err(err) = crate::task::manager_sync::sync_current_track(&state).await {
                return Err(format!("实时轨迹同步失败: {err}"));
            }
        }
        ("trackTask", "syncSuspiciousCar") => {
            if let Err(err) = crate::task::manager_sync::sync_suspicious_car(&state, &[]).await {
                return Err(format!("可疑车辆同步失败: {err}"));
            }
        }
        ("trackTask", "syncHistoryTrack") => log_count(
            "历史轨迹",
            crate::task::manager_sync::sync_history_track(&state).await,
        ),
        ("trackTask", "saveCarExcept") => log_count(
            "逃费金额回写",
            crate::task::manager_sync::save_car_except(&state).await,
        ),
        // Java: TrackTask.syncHistoryTrackNoCar 方法体全部注释，等价于空操作。
        ("trackTask", "syncHistoryTrackNoCar") => {
            tracing::info!("[定时任务] trackTask.syncHistoryTrackNoCar（方法体已注释，跳过）");
        }
        ("trackTask", "changeCarSuspicious") => {
            match crate::task::manager_sync::change_car_suspicious(&state).await {
                Ok((moved, removed)) => {
                    tracing::info!(
                        "[定时任务] 可疑车辆迁移完成，迁移 {} 条，删除 {} 条",
                        moved,
                        removed
                    );
                }
                Err(err) => return Err(format!("可疑车辆迁移失败: {err}")),
            }
        }
        // bean/方法都存在，但 Rust 侧还没有对应的实现（远端接口或空转逻辑）。
        (other, method) => {
            return Err(format!(
                "任务 {other}.{method} 尚未迁移（依赖远端 HttpBaseInfoApiService / 轨迹同步），已跳过"
            ));
        }
    }
    Ok(())
}
