package com.ruoyi.base.domain;

import java.math.BigDecimal;
import java.util.Date;

import com.baomidou.mybatisplus.annotation.IdType;
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
 * 收费站出口流水对象 ods_lwzxsfsj_fee_station_exit_01
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@Data
@TableName("ods_lwzxsfsj_fee_station_exit_01")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class OdsLwzxsfsjFeeStationExit01 implements Custom {

    /** 主键 */
    @TableId(value = "bigId", type = IdType.ASSIGN_UUID)
    private String bigId;

    /** 实际计费方式 */
    @Excel(name = "实际计费方式")
    private String actualfeeclass;

    /** 车轴数 */
    @Excel(name = "车轴数")
    private Integer axlecount;

    /** 优惠金额 */
    @Excel(name = "优惠金额")
    private Long discountfee;

    /** 单片式OBU/CPC卡电量百分比 */
    @Excel(name = "单片式OBU/CPC卡电量百分比")
    private Integer electricalpercentage;

    /** 入站车轴数 */
    @Excel(name = "入站车轴数")
    private Integer enaxlecount;

    /** 进站时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "进站时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date entime;

    /** 入口车道hex */
    @Excel(name = "入口车道hex")
    private String entolllanehex;

    /** 进站收费站车道号 */
    @Excel(name = "进站收费站车道号")
    private String entolllaneid;

    /** 入口收费站编码 */
    @Excel(name = "入口收费站编码")
    private String entollstationid;

    /** 入口收费站名称 */
    @Excel(name = "入口收费站名称")
    private String entollstationname;

    /** 入口车种 */
    @Excel(name = "入口车种")
    private Integer envehicleclass;

    /** 入口车牌号+车牌类型 */
    @Excel(name = "入口车牌号+车牌类型")
    private String envehicleid;

    /** 入口车型 */
    @Excel(name = "入口车型")
    private Integer envehicletype;

    /** 入口称重 */
    @Excel(name = "入口称重")
    private Long enweight;

    /** 入口操作人员id */
    @Excel(name = "入口操作人员id")
    private String entryoperatorid;

    /** 出站时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "出站时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date extime;

    /** 出口车道号编码 */
    @Excel(name = "出口车道号编码")
    private String extolllaneid;

    /** 出口收费站编码 */
    @Excel(name = "出口收费站编码")
    private String extollstationid;

    /** 出口收费站名称 */
    @Excel(name = "出口收费站名称")
    private String extollstationname;

    /** 出口车种 */
    @Excel(name = "出口车种")
    private Integer exvehicleclass;

    /** 出口车牌号+车牌类型 */
    @Excel(name = "出口车牌号+车牌类型")
    private String exvehicleid;

    /** 出口车型 */
    @Excel(name = "出口车型")
    private Integer exvehicletype;

    /** 费用 */
    @Excel(name = "费用")
    private Long fee;

    /** 出口称重 */
    @Excel(name = "出口称重")
    private Long exweight;

    /** 费显显示信息 */
    @Excel(name = "费显显示信息")
    private String feeboardplay;

    /** 收费里程 */
    @Excel(name = "收费里程")
    private Long feemileage;

    /** 开票标识 */
    @Excel(name = "开票标识")
    private String identification;

    /** 交易金额占比 */
    @Excel(name = "交易金额占比")
    private BigDecimal feerate;

    /** 车牌号+车牌类型 */
    @Excel(name = "车牌号+车牌类型")
    private String identifyvehicleid;

    /** 车道类型 */
    @Excel(name = "车道类型")
    private String lanetype;

    /** 介质编码 */
    @Excel(name = "介质编码")
    private String mediano;

    /** 通行介质类型 */
    @Excel(name = "通行介质类型")
    private String mediatype;

    /** 标签无卡累计次数 */
    @Excel(name = "标签无卡累计次数")
    private Integer nocardcount;

    /** OBU序号编码 */
    @Excel(name = "OBU序号编码")
    private String obuid;

    /** OBU 单/双片标识 */
    @Excel(name = "OBU 单/双片标识")
    private String obusign;

    /** 0BU 总累计交易金额 */
    @Excel(name = "0BU 总累计交易金额")
    private Long obutotalamount;

    /** OBU累计优惠后通行费金额 */
    @Excel(name = "OBU累计优惠后通行费金额")
    private Long obutotaldiscountamount;

    /** 参数 */
    @Excel(name = "参数")
    private String params;

    /** 操作id */
    @Excel(name = "操作id")
    private String operid;

    /** 通行id */
    @Excel(name = "通行id")
    private String passid;

    /** 支付id */
    @Excel(name = "支付id")
    private String paycardid;

    /** 应收金额 */
    @Excel(name = "应收金额")
    private Long payfee;

    /** 支付类型 */
    @Excel(name = "支付类型")
    private String paytype;

    /** $column.columnComment */
    @Excel(name = "${comment}", readConverterExp = "$column.readConverterExp()")
    private Long provfee;

    /** 本省交易成功次数 */
    @Excel(name = "本省交易成功次数")
    private Integer provtranscount;

    /** 通行省份个数 */
    @Excel(name = "通行省份个数")
    private Integer provincecount;

    /** 工班号 */
    @Excel(name = "工班号")
    private String shift;

    /** 接收时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "接收时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date receivetime;

    /** 最短收费金额 */
    @Excel(name = "最短收费金额")
    private Long shortfee;

    /** 最短路径里程数 */
    @Excel(name = "最短路径里程数")
    private Long shortfeemileage;

    /** 标记状态 */
    @Excel(name = "标记状态")
    private String signstatus;

    /** 全网最小费额费率版本号 */
    @Excel(name = "全网最小费额费率版本号")
    private String spcrateversion;

    /** TAC码 */
    @Excel(name = "TAC码")
    private String tac;

    /** 特殊类型 */
    @Excel(name = "特殊类型")
    private String specialtype;

    /** 多条省内交易信息 */
    @Excel(name = "多条省内交易信息")
    private String splitprovince;

    /** 终端机编号 */
    @Excel(name = "终端机编号")
    private String terminalno;

    /** PSAM卡脱机交易序列号 */
    @Excel(name = "PSAM卡脱机交易序列号")
    private String terminaltransno;

    /** 卡面扣费金额 */
    @Excel(name = "卡面扣费金额")
    private Long transfee;

    /** 交易支付类型 */
    @Excel(name = "交易支付类型")
    private String transpaytype;

    /** 交易类型标识 */
    @Excel(name = "交易类型标识")
    private String transtype;

    /** 加载时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "加载时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date loadTime;

    /** 车辆状态标识 */
    @Excel(name = "车辆状态标识")
    private String vehiclesign;

    /** 分类分级 */
    @Excel(name = "分类分级")
    private String gradeLevel;

    /** 车牌识别流水号 */
    @Excel(name = "车牌识别流水号")
    private String vehiclesignid;


}
