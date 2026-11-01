// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsRtSzdnSnapshotFlowProvcaptureAddcodeController.java
//       ruoyi-system/src/main/resources/mapper/base/OdsRtSzdnSnapshotFlowProvcaptureAddcodeMapper.xml
// 职责: 省界抓拍只读查询。
// 对应关系: selectOdsRtSzdnSnapshotFlowProvcaptureAddcodeList/ById -> SPEC。

use axum::extract::{Path, RawQuery, State};
use axum::Router;
use serde_json::Value;

use crate::api::meta;
use crate::api::support::{self, FieldFormat, Filter, ListSpec};
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const SPEC: ListSpec = ListSpec {
    select: "t.big_id, t.deviceip, t.tailcapturetimeunix, t.tailcapturetime, t.extendattribute, \
             t.smallsideimagewidth, t.axletype, t.smallsideimageheight, t.platecolorcode, \
             t.platecolor, t.cover, t.averageauthoritative, t.headlanecode, t.specialvehicle, \
             t.carlength, t.resulttype, t.carhight, t.carmodelscode, t.carmodels, \
             t.laneposition, t.firstauthoritative, t.tailplateimageheight, t.axlecount, \
             t.plateimagewidth, t.specialclass, t.tailplatenumber, t.tailimage, \
             t.sidecapturetimeunix, t.sidecapturetime, t.sidelanecode, t.wheelbase, t.attached, \
             t.wheelcount, t.guid, t.sideimagewidth, t.plateimageheight, t.datasource, \
             t.carclass, t.gantryid, t.smallsideimage, t.headimageheight, t.sidescenetypecode, \
             t.sidescenetype, t.tailimagewidth, t.envstate, t.headscenetypecode, \
             t.headscenetype, t.sidedrivingdirectioncode, t.sidedrivingdirection, \
             t.sideimageheight, t.speed, t.tailplateimage, t.headdrivingdirectioncode, \
             t.headdrivingdirection, t.cartype, t.plateimage, t.changelane, t.sideimage, \
             t.tailplateposition, t.headimagewidth, t.headimage, t.carweight, \
             t.tailimageheight, t.devicecode, t.platenumber, t.tailplatecolorcode, \
             t.tailplatecolor, t.uploadtimeunix, t.uploadtime, t.impostoraxlecount, \
             t.taillanecode, t.siteid, t.headcapturetimeunix, t.headcapturetime, \
             t.plateposition, t.tailplateimagewidth, t.loadtime, t.gradelevel, t.datauuid, \
             t.reserve1, t.reserve2, t.reserve3",
    from: "from ods_rt_szdn_snapshot_flow_provcapture_addcode t",
    filters: &[
        Filter::eq("bigId", "t.big_id"),
        Filter::eq("deviceip", "t.deviceip"),
        Filter::eq("tailcapturetimeunix", "t.tailcapturetimeunix"),
        Filter::eq("tailcapturetime", "t.tailcapturetime"),
        Filter::eq("extendattribute", "t.extendattribute"),
        Filter::eq("smallsideimagewidth", "t.smallsideimagewidth"),
        Filter::eq("axletype", "t.axletype"),
        Filter::eq("smallsideimageheight", "t.smallsideimageheight"),
        Filter::eq("platecolorcode", "t.platecolorcode"),
        Filter::eq("platecolor", "t.platecolor"),
        Filter::eq("cover", "t.cover"),
        Filter::eq("averageauthoritative", "t.averageauthoritative"),
        Filter::eq("headlanecode", "t.headlanecode"),
        Filter::eq("specialvehicle", "t.specialvehicle"),
        Filter::eq("carlength", "t.carlength"),
        Filter::eq("resulttype", "t.resulttype"),
        Filter::eq("carhight", "t.carhight"),
        Filter::eq("carmodelscode", "t.carmodelscode"),
        Filter::eq("carmodels", "t.carmodels"),
        Filter::eq("laneposition", "t.laneposition"),
        Filter::eq("firstauthoritative", "t.firstauthoritative"),
        Filter::eq("tailplateimageheight", "t.tailplateimageheight"),
        Filter::eq("axlecount", "t.axlecount"),
        Filter::eq("plateimagewidth", "t.plateimagewidth"),
        Filter::eq("specialclass", "t.specialclass"),
        Filter::eq("tailplatenumber", "t.tailplatenumber"),
        Filter::eq("tailimage", "t.tailimage"),
        Filter::eq("sidecapturetimeunix", "t.sidecapturetimeunix"),
        Filter::eq("sidecapturetime", "t.sidecapturetime"),
        Filter::eq("sidelanecode", "t.sidelanecode"),
        Filter::eq("wheelbase", "t.wheelbase"),
        Filter::eq("attached", "t.attached"),
        Filter::eq("wheelcount", "t.wheelcount"),
        Filter::eq("guid", "t.guid"),
        Filter::eq("sideimagewidth", "t.sideimagewidth"),
        Filter::eq("plateimageheight", "t.plateimageheight"),
        Filter::eq("datasource", "t.datasource"),
        Filter::eq("carclass", "t.carclass"),
        Filter::eq("gantryid", "t.gantryid"),
        Filter::eq("smallsideimage", "t.smallsideimage"),
        Filter::eq("headimageheight", "t.headimageheight"),
        Filter::eq("sidescenetypecode", "t.sidescenetypecode"),
        Filter::eq("sidescenetype", "t.sidescenetype"),
        Filter::eq("tailimagewidth", "t.tailimagewidth"),
        Filter::eq("envstate", "t.envstate"),
        Filter::eq("headscenetypecode", "t.headscenetypecode"),
        Filter::eq("headscenetype", "t.headscenetype"),
        Filter::eq("sidedrivingdirectioncode", "t.sidedrivingdirectioncode"),
        Filter::eq("sidedrivingdirection", "t.sidedrivingdirection"),
        Filter::eq("sideimageheight", "t.sideimageheight"),
        Filter::eq("speed", "t.speed"),
        Filter::eq("tailplateimage", "t.tailplateimage"),
        Filter::eq("headdrivingdirectioncode", "t.headdrivingdirectioncode"),
        Filter::eq("headdrivingdirection", "t.headdrivingdirection"),
        Filter::eq("cartype", "t.cartype"),
        Filter::eq("plateimage", "t.plateimage"),
        Filter::eq("changelane", "t.changelane"),
        Filter::eq("sideimage", "t.sideimage"),
        Filter::eq("tailplateposition", "t.tailplateposition"),
        Filter::eq("headimagewidth", "t.headimagewidth"),
        Filter::eq("headimage", "t.headimage"),
        Filter::eq("carweight", "t.carweight"),
        Filter::eq("tailimageheight", "t.tailimageheight"),
        Filter::eq("devicecode", "t.devicecode"),
        Filter::eq("platenumber", "t.platenumber"),
        Filter::eq("tailplatecolorcode", "t.tailplatecolorcode"),
        Filter::eq("tailplatecolor", "t.tailplatecolor"),
        Filter::eq("uploadtimeunix", "t.uploadtimeunix"),
        Filter::eq("uploadtime", "t.uploadtime"),
        Filter::eq("impostoraxlecount", "t.impostoraxlecount"),
        Filter::eq("taillanecode", "t.taillanecode"),
        Filter::eq("siteid", "t.siteid"),
        Filter::eq("headcapturetimeunix", "t.headcapturetimeunix"),
        Filter::eq("headcapturetime", "t.headcapturetime"),
        Filter::eq("plateposition", "t.plateposition"),
        Filter::eq("tailplateimagewidth", "t.tailplateimagewidth"),
        Filter::eq("loadtime", "t.loadtime"),
        Filter::eq("gradelevel", "t.gradelevel"),
        Filter::eq("datauuid", "t.datauuid"),
        Filter::eq("reserve1", "t.reserve1"),
        Filter::eq("reserve2", "t.reserve2"),
        Filter::eq("reserve3", "t.reserve3"),
    ],
    extra_where: "",
    order_by: "t.big_id",
    id_column: "t.big_id",
};

// Java 实体字段类型：uploadtime/headcapturetime/sidecapturetime 为 LocalDate，
// tailcapturetime/loadtime 为 java.util.Date（Jackson 默认 ISO+时区）。
const FORMATS: &[(&str, FieldFormat)] = &[
    ("uploadtime", FieldFormat::DateOnly),
    ("headcapturetime", FieldFormat::DateOnly),
    ("sidecapturetime", FieldFormat::DateOnly),
    ("tailcapturetime", FieldFormat::IsoOffset),
    ("loadtime", FieldFormat::IsoOffset),
];

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/base/provcapture/list",
            meta::get_route("/base/provcapture/list", None, None, list),
        )
        .route(
            "/base/provcapture/{bigId}",
            meta::get_route("/base/provcapture/{bigId}", None, None, get_info),
        )
}

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let page = support::page_domain(&raw);
    let params = support::query_map(&raw);
    let (total, rows) = support::query_list_fmt(&state.db, &params, &SPEC, &page, FORMATS).await?;
    Ok(TableDataInfo::new(total, rows))
}

async fn get_info(
    State(state): State<AppState>,
    Path(big_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    Ok(AjaxResult::success_data(
        support::query_by_id_fmt(&state.db, &SPEC, &big_id, FORMATS).await?,
    ))
}
