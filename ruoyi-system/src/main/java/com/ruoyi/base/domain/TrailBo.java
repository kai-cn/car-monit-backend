package com.ruoyi.base.domain;

import lombok.Data;

import java.math.BigDecimal;

@Data
public class TrailBo {

    //  流水唯一标识符:用于标识单条抓拍或收费流水的唯一性，支持去重、追踪和跨表关联
    private String pointUuid;

    /**
     *  流水来源类型标识:可作为维度字段，用于回溯数据来源、确定查找目标表：
     *  省界称重：BorderWeighingCapture
     *  门架抓拍 GantryCapture
     *  省界抓拍 ProvCapture
     *  服务区抓拍  ServiceAreaCapture
     *  收费站抓拍 StationCapture
     */
    private String stateType;

    // 是否有值 O否 1是
    private String pointFlag;

    // pointUuid josn对象
    private String pointJosn;

    OdsSzdnProvinceBorderVehicleWeightNewstructure  borderWeighingCaptureBO;  // 省界称重

    OdsRtSzdnSnapshotFlowAddcode  gantryCaptureBO;  // 门架抓拍

    OdsRtSzdnSnapshotFlowProvcaptureAddcode  provCaptureBO;  // 省界抓拍

    OdsRtSzdnSnapshotFlowStationcaptureAddcode  stationCapture;  // 收费站抓拍

    OdsLwzxsfsjFeeRecords01  feeRecord; // 卡口流水

    OdsLwzxsfsjFeeStationEnter01  feeStationEnter; // 收费站入口流水

    OdsLwzxsfsjFeeStationExit01  feeStationExit; // 收费站出口流水


    // 抓拍流水发生时间:用于轨迹拼接、排序和时序分析
    private String captureTime;

    // 车辆在收费站的进出方向:用于区分车流方向，支撑进出站逻辑和轨迹起止点判定  true=进入，false=驶出，null=非进出类
    private Boolean directionIn;

    // 设备IP地址:可通过映射表解析IP→实体设施（门架、收费站、服务区等），实现设备到道路设施的转换
    private String locationCode;

    // 位置是否有值
    private String locationFlag;

    /**
     *  ip类型 :
     *  gantryip 门架ip
     *  stationip 收费站ip
     */
    private String ipType;

    // 位置josn 对象
    private String locationJosn;

    OdsSzdnGantryIp  gantryIpBO; // 门架IP

    OdsSzdnTollStationIp  stationIpBO;  // 收费站ip


    // 设备编码
    private String devCode;

    // 设备名称
    private String devName;

    // 抓拍图片
    private String imagesArry;

    /** 经度 */
    private BigDecimal lon;

    /** 维度 */
    private BigDecimal lat;

    /** 路线编号 */
    private String roadCode;

    /** 路段编号 */
    private String sectionCode;

    /** 方向（0: 上行，1: 下行） */
    private String direction;

    /** 桩号 */
    private String pileno;

    // 上一个抓拍时间
    private String preCaptureTime;

    // 数量
    private Integer countNum;

    /** 桩号 */
    private BigDecimal pilenoDec;

    /** 是否查询：1查询 */
    private String isQuery;

}
