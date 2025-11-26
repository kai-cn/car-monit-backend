package com.ruoyi.base.domain;

import java.math.BigDecimal;
import java.util.Date;
import java.util.List;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.fasterxml.jackson.annotation.JsonFormat;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BasePlusEntity;
import com.ruoyi.common.core.domain.Custom;

/**
 * 基础-收费流水对象 ods_lwzxsfsj_fee_records_01
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@Data
@TableName("ods_lwzxsfsj_fee_records_01")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class OdsLwzxsfsjFeeRecords01 implements Custom {

    /** 主键 */
    @TableId(value = "big_id", type = IdType.ASSIGN_UUID)
    private String bigId;

    /** 算法标识 */
    @Excel(name = "算法标识")
    private String algorithmidentifier;

    /** 天线ID编号(天线头编号) */
    @Excel(name = "天线ID编号(天线头编号)")
    private String antennaid;

    /** 车轴数 */
    @Excel(name = "车轴数")
    private Long axlecount;

    /** 交易后余额 */
    @Excel(name = "交易后余额")
    private BigDecimal balanceafter;

    /** 交易前余额 */
    @Excel(name = "交易前余额")
    private BigDecimal balancebefore;

    /** 本次交易后卡片累计金额 */
    @Excel(name = "本次交易后卡片累计金额")
    private BigDecimal cardfeesumafter;

    /** 本次交易前卡片累计金额 */
    @Excel(name = "本次交易前卡片累计金额")
    private BigDecimal cardfeesumbefore;

    /** 控制器序号 */
    @Excel(name = "控制器序号")
    private String computerorder;

    /** 交易耗时（单位：ms） */
    @Excel(name = "交易耗时", readConverterExp = "单=位：ms")
    private Long consumetime;

    /** CPU卡编号 */
    @Excel(name = "CPU卡编号")
    private String cpucardid;

    /** CPU卡类型 */
    @Excel(name = "CPU卡类型")
    private String cpucardtype;

    /** CPU截止日期 */
    @Excel(name = "CPU截止日期")
    private String cpuenddate;

    /** CPU卡片发行方标识 */
    @Excel(name = "CPU卡片发行方标识")
    private String cpuissueid;

    /** CPU卡片网络编号 */
    @Excel(name = "CPU卡片网络编号")
    private String cpunetid;

    /** CPU起始日期 */
    @Excel(name = "CPU起始日期")
    private String cpustartdate;

    /** CPU 内车牌号码 */
    @Excel(name = "CPU 内车牌号码")
    private String cpuvehicleplate;

    /** CPU内车型 */
    @Excel(name = "CPU内车型")
    private String cpuvehicletype;

    /** CPU用户卡版本号 */
    @Excel(name = "CPU用户卡版本号")
    private String cpuversion;

    /** 处理状态 */
    @Excel(name = "处理状态")
    private String dealstatus;

    /** 优惠金额 */
    @Excel(name = "优惠金额")
    private BigDecimal discountfee;

    /** 优惠金额组合 */
    @Excel(name = "优惠金额组合")
    private String discountfeegroup;

    /** 入口车道类型 */
    @Excel(name = "入口车道类型")
    private String enlanetype;

    /** 进站时间 */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @Excel(name = "进站时间", width = 30, dateFormat = "yyyy-MM-dd  HH:mm:ss")
    private Date entime;

    /** 进站收费站车道号 */
    @Excel(name = "进站收费站车道号")
    private String entolllaneid;

    /** 进站收费站hex编码 */
    @Excel(name = "进站收费站hex编码")
    private String entollstationhex;

    /** 费用 */
    @Excel(name = "费用")
    private BigDecimal fee;

    /** 计费模块响应计费结果 */
    @Excel(name = "计费模块响应计费结果")
    private String feecalcresult;

    /** 计费接口特情值 */
    @Excel(name = "计费接口特情值")
    private String feecalcspecial;

    /** 计费特情值组合 */
    @Excel(name = "计费特情值组合")
    private String feecalcspecials;

    /** 交易金额组合 */
    @Excel(name = "交易金额组合")
    private String feegroup;

    /** 计费信息1 */
    @Excel(name = "计费信息1")
    private String feeinfo1;

    /** 计费信息2 */
    @Excel(name = "计费信息2")
    private String feeinfo2;

    /** 计费信息3 */
    @Excel(name = "计费信息3")
    private String feeinfo3;

    /** 收费里程 */
    @Excel(name = "收费里程")
    private BigDecimal feemileage;

    /** 本省计费起点 */
    @Excel(name = "本省计费起点")
    private String feeprovbeginhex;

    /** 计费协议保留字段1 */
    @Excel(name = "计费协议保留字段1")
    private String feespare1;

    /** 计费协议保留字段2 */
    @Excel(name = "计费协议保留字段2")
    private String feespare2;

    /** 计费车型 */
    @Excel(name = "计费车型")
    private String feevehicletype;

    /** 门架Hex值 */
    @Excel(name = "门架Hex值")
    private String gantryhex;

    /** 对向门架Hex值 */
    @Excel(name = "对向门架Hex值")
    private String gantryhexopposite;

    /** 门架编码 */
    @Excel(name = "门架编码")
    private String gantryid;

    /** 门架顺序号 */
    @Excel(name = "门架顺序号")
    private Long gantryordernum;

    /** 门架类型 */
    @Excel(name = "门架类型")
    private String gantrytype;

    /** 节假日状态 */
    @Excel(name = "节假日状态")
    private String holidaystate;

    /** 小时批次号 */
    @Excel(name = "小时批次号")
    private String hourbatchno;

    /** 消费密钥版本号 */
    @Excel(name = "消费密钥版本号")
    private String keyversion;

    /** 上一个门架的hex编号 */
    @Excel(name = "上一个门架的hex编号")
    private String lastgantryhex;

    /** 通过上一个门架的时间 */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @Excel(name = "通过上一个门架的时间", width = 30, dateFormat = "yyyy-MM-dd HH:mm:ss")
    private Date lastgantrytime;

    /** 匹配状态 */
    @Excel(name = "匹配状态")
    private String matchstatus;

    /** 通行介质类型 */
    @Excel(name = "通行介质类型")
    private String mediatype;

    /** 本次交易后累计无卡次数 */
    @Excel(name = "本次交易后累计无卡次数")
    private Long nocardtimesafter;

    /** 本次交易前累计无卡次数 */
    @Excel(name = "本次交易前累计无卡次数")
    private Long nocardtimesbefore;

    /** OBU/CPC卡电量百分比 */
    @Excel(name = "OBU/CPC卡电量百分比")
    private Long obuelectrical;

    /** OBU/CPC截止日期 */
    @Excel(name = "OBU/CPC截止日期")
    private String obuenddate;

    /** 本次交易后标签累计实收金额 */
    @Excel(name = "本次交易后标签累计实收金额")
    private BigDecimal obufeesumafter;

    /** 本次交易前标签累计实收金额 */
    @Excel(name = "本次交易前标签累计实收金额")
    private BigDecimal obufeesumbefore;

    /** 读取标签入口信息类型 */
    @Excel(name = "读取标签入口信息类型")
    private String obuinfotyperead;

    /** 本次写入标签入口信息类型 */
    @Excel(name = "本次写入标签入口信息类型")
    private String obuinfotypewrite;

    /** OBU/CPC发行方标识 */
    @Excel(name = "OBU/CPC发行方标识")
    private String obuissueid;

    /** OBU中上一个门架HEX */
    @Excel(name = "OBU中上一个门架HEX")
    private String obulastgantryhex;

    /** OBU中通过上一个门架时间 */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @Excel(name = "OBU中通过上一个门架时间", width = 30, dateFormat = "yyyy-MM-dd HH:mm:ss")
    private Date obulastgantrytime;

    /** OBU /CPC物理地址 */
    @Excel(name = "OBU /CPC物理地址")
    private String obumac;

    /** 本次交易后标签累计里程 */
    @Excel(name = "本次交易后标签累计里程")
    private BigDecimal obumileageafter;

    /** 本次交易前标签累计里程 */
    @Excel(name = "本次交易前标签累计里程")
    private BigDecimal obumileagebefore;

    /** 标签入口状态 */
    @Excel(name = "标签入口状态")
    private String obupassstate;

    /** 本次交易后标签累计应收金额 */
    @Excel(name = "本次交易后标签累计应收金额")
    private BigDecimal obupayfeesumafter;

    /** 本次交易前标签累计应收金额 */
    @Excel(name = "本次交易前标签累计应收金额")
    private BigDecimal obupayfeesumbefore;

    /** 本次交易后标签累计金额（省内） */
    @Excel(name = "本次交易后标签累计金额", readConverterExp = "省=内")
    private BigDecimal obuprovfeesumafter;

    /** 本次交易前标签累计金额 （省内） */
    @Excel(name = "本次交易前标签累计金额 ", readConverterExp = "省=内")
    private BigDecimal obuprovfeesumbefore;

    /** 本次交易后标签累计应收金额（省内） */
    @Excel(name = "本次交易后标签累计应收金额", readConverterExp = "省=内")
    private BigDecimal obuprovpayfeesumafter;

    /** 本次交易前标签累计应收金额（省内） */
    @Excel(name = "本次交易前标签累计应收金额", readConverterExp = "省=内")
    private BigDecimal obuprovpayfeesumbefore;

    /** 省内本次交易后标签累计写入成功数量 */
    @Excel(name = "省内本次交易后标签累计写入成功数量")
    private Long obuprovtradesuccnumafter;

    /** 省内本次交易前标签累计写入成功数量 */
    @Excel(name = "省内本次交易前标签累计写入成功数量")
    private Long obuprovtradesuccnumbefore;

    /** OBU 单/双片标识 */
    @Excel(name = "OBU 单/双片标识")
    private String obusign;

    /** OBU/CPC序号编码 */
    @Excel(name = "OBU/CPC序号编码")
    private String obusn;

    /** OBU/CPC起始日期 */
    @Excel(name = "OBU/CPC起始日期")
    private String obustartdate;

    /** OBU/CPC状态 */
    @Excel(name = "OBU/CPC状态")
    private String obustate;

    /** 本次交易后标签累计写入成功总量 */
    @Excel(name = "本次交易后标签累计写入成功总量")
    private Long obutotaltradesuccnumafter;

    /** 本次交易前标签累计写入成功总量 */
    @Excel(name = "本次交易前标签累计写入成功总量")
    private Long obutotaltradesuccnumbefore;

    /** 标签写入结果 */
    @Excel(name = "标签写入结果")
    private String obutraderesult;

    /** obu车牌 */
    @Excel(name = "obu车牌")
    private String obuvehicleplate;

    /** obu车牌类型 */
    @Excel(name = "obu车牌类型")
    private String obuvehicletype;

    /** OBU/CPC版本号 */
    @Excel(name = "OBU/CPC版本号")
    private String obuversion;

    /** 参数 */
    @Excel(name = "参数")
    private String params;

    /** 通行id */
    @Excel(name = "通行id")
    private String passid;

    /** 通行状态 */
    @Excel(name = "通行状态")
    private String passstate;

    /** 本次计费拟合结果标识 */
    @Excel(name = "本次计费拟合结果标识")
    private String pathfitflag;

    /** 应收金额 */
    @Excel(name = "应收金额")
    private BigDecimal payfee;

    /** 应收金额组合 */
    @Excel(name = "应收金额组合")
    private String payfeegroup;

    /** PC-RSU接口协议版本号 */
    @Excel(name = "PC-RSU接口协议版本号")
    private String pcrsuversion;

    /** 本省累计通行金额参考 */
    @Excel(name = "本省累计通行金额参考")
    private BigDecimal provminfee;

    /** 本次交易后累计省份数量 */
    @Excel(name = "本次交易后累计省份数量")
    private Long provincenumafter;

    /** 本次交易前累计省份数量 */
    @Excel(name = "本次交易前累计省份数量")
    private Long provincenumbefore;

    /** 计费模块计费模式 */
    @Excel(name = "计费模块计费模式")
    private String ratecompute;

    /** 计费模块拟合点总数 */
    @Excel(name = "计费模块拟合点总数")
    private Long ratefitcount;

    /** 计费模块和计费参数版本号 */
    @Excel(name = "计费模块和计费参数版本号")
    private String rateversion;

    /** 本次交易读取的EF04加密摘要验证结果 */
    @Excel(name = "本次交易读取的EF04加密摘要验证结果")
    private String readciphertextverify;

    /** 接收时间 */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @Excel(name = "接收时间", width = 30, dateFormat = "yyyy-MM-dd HH:mm:ss")
    private Date receivetime;

    /** 交易的服务类型 */
    @Excel(name = "交易的服务类型")
    private String servicetype;

    /** 门架后台入库时间 */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @Excel(name = "门架后台入库时间", width = 30, dateFormat = "yyyy-MM-dd HH:mm:ss")
    private Date stationdbtime;

    /** 门架后台处理时间 */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @Excel(name = "门架后台处理时间", width = 30, dateFormat = "yyyy-MM-dd HH:mm:ss")
    private Date stationdealtime;

    /** 门架后台匹配时间 */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @Excel(name = "门架后台匹配时间", width = 30, dateFormat = "yyyy-MM-dd HH:mm:ss")
    private Date stationmatchtime;

    /** 门架后台去重时间 */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @Excel(name = "门架后台去重时间", width = 30, dateFormat = "yyyy-MM-dd HH:mm:ss")
    private Date stationvalidtime;

    /** TAC码 */
    @Excel(name = "TAC码")
    private String tac;

    /** 终端机编号 */
    @Excel(name = "终端机编号")
    private String terminalno;

    /** PSAM卡脱机交易序列号 */
    @Excel(name = "PSAM卡脱机交易序列号")
    private String terminaltransno;

    /** 收费单元编号组合 */
    @Excel(name = "收费单元编号组合")
    private String tollintervalid;

    /** 收费单元处理标识 */
    @Excel(name = "收费单元处理标识")
    private String tollintervalsign;

    /** 车货总重 */
    @Excel(name = "车货总重")
    private BigDecimal totalweight;

    /** 计费交易编号 */
    @Excel(name = "计费交易编号")
    private String tradeid;

    /** 本次交易读取的EF04加密摘要 */
    @Excel(name = "本次交易读取的EF04加密摘要")
    private String tradereadciphertext;

    /** 卡片复合交易结果 */
    @Excel(name = "卡片复合交易结果")
    private String traderesult;

    /** 交易类型 */
    @Excel(name = "交易类型")
    private String tradetype;

    /** 本次交易生成的EF04加密摘要 */
    @Excel(name = "本次交易生成的EF04加密摘要")
    private String tradewriteciphertext;

    /** 卡面扣费金额 */
    @Excel(name = "卡面扣费金额")
    private BigDecimal transfee;

    /** IC卡交易序号 */
    @Excel(name = "IC卡交易序号")
    private String transno;

    /** 计费交易时间 */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @Excel(name = "计费交易时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date transtime;

    /** 交易类型标识 */
    @Excel(name = "交易类型标识")
    private String transtype;

    /** 去重状态 */
    @Excel(name = "去重状态")
    private String validstatus;

    /** 车种 */
    @Excel(name = "车种")
    private String vehicleclass;

    /** 车高 */
    @Excel(name = "车高")
    private BigDecimal vehiclehight;

    /** 车长 */
    @Excel(name = "车长")
    private BigDecimal vehiclelength;

    /** 车牌号+类型 */
    @Excel(name = "车牌号+类型")
    private String vehicleplate;

    /** 车辆座位数/载重 */
    @Excel(name = "车辆座位数/载重")
    private String vehicleseat;

    /** 车辆状态标识 */
    @Excel(name = "车辆状态标识")
    private String vehiclesign;

    /** 车辆类型 */
    @Excel(name = "车辆类型")
    private String vehicletype;

    /** 车辆用户类型 */
    @Excel(name = "车辆用户类型")
    private String vehicleusertype;

    /** 车宽 */
    @Excel(name = "车宽")
    private BigDecimal vehiclewidth;

    /** 校验码 */
    @Excel(name = "校验码")
    private String verifycode;

    /** 加载时间 */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @Excel(name = "加载时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date loadTime;

    /** 分类分级 */
    @Excel(name = "分类分级")
    private Long gradeLevel;

    /** cid */
    @Excel(name = "cid")
    private String cid;

    @TableField(exist = false)
    private List<String> cidList;

    // 时间查询
    @TableField(exist = false)
    private String inApplyTime1;

    @TableField(exist = false)
    private String inApplyTime2;

    @TableField(exist = false)
    private String outApplyTime1;

    @TableField(exist = false)
    private String outApplyTime2;

    // 当前页面
    @TableField(exist = false)
    private Integer pageNum;

    // 分页大小
    @TableField(exist = false)
    private Integer pageSize;

    @TableField(exist = false)
    private String plateColor;

    /** 门架名称 */
    @TableField(exist = false)
    private String gantryName;

    @TableField(exist = false)
    private String receivetimeStr;



    /** 所属路段编码 */
    @TableField(exist = false)
    private String sectionCodeStr;

    /**
     * 1收费站、2门架、3服务区
     */
    @TableField(exist = false)
    private String type;

    /**
     * 编码
     */
    @TableField(exist = false)
    private String code;

    @TableField(exist = false)
    private String sectionName;


    @TableField(exist = false)
    private String roadname;

    /**
     * 计费交易时间
     */
    @TableField(exist = false)
    private String transtimeStr;

    /**
     * 通过上一个门架的时间
     */
    @TableField(exist = false)
    private String lastgantrytimeStr;

    //收费状态
    @TableField(exist = false)
    private String chargeStatus;

    //收费状态
    @TableField(exist = false)
    private String chargeStatusStr;
}
