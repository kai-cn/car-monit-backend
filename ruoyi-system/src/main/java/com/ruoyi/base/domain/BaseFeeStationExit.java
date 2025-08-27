package com.ruoyi.base.domain;

import java.math.BigDecimal;
import java.util.Date;
import com.fasterxml.jackson.annotation.JsonFormat;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BasePlusEntity;
import com.ruoyi.common.core.domain.Custom;

/**
 * 收费站出口流水对象 base_fee_station_exit
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Data
@TableName("base_fee_station_exit")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class BaseFeeStationExit extends BasePlusEntity implements Custom {

    /** 主键 */
    private String bigId;

    /** 实际计费方式 */
    @Excel(name = "实际计费方式")
    private String actualFeeClass;

    /** 车轴数 */
    @Excel(name = "车轴数")
    private Integer axleCount;

    /** 优惠金额 */
    @Excel(name = "优惠金额")
    private Long discountFee;

    /** 单片式OBU/CPC卡电量百分比 */
    @Excel(name = "单片式OBU/CPC卡电量百分比")
    private Integer electricalPercentage;

    /** 入站车轴数 */
    @Excel(name = "入站车轴数")
    private Integer enAxleCount;

    /** 进站时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "进站时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date enTime;

    /** 入口车道hex */
    @Excel(name = "入口车道hex")
    private String enTollLaneHex;

    /** 进站收费站车道号 */
    @Excel(name = "进站收费站车道号")
    private String enTollLaneId;

    /** 入口收费站编码 */
    @Excel(name = "入口收费站编码")
    private String enTollStationId;

    /** 入口收费站名称 */
    @Excel(name = "入口收费站名称")
    private String enTollStationName;

    /** 入口车种 */
    @Excel(name = "入口车种")
    private Integer enVehicleClass;

    /** 入口车牌号+车牌类型 */
    @Excel(name = "入口车牌号+车牌类型")
    private String enVehicleId;

    /** 入口车型 */
    @Excel(name = "入口车型")
    private Integer enVehicleType;

    /** 入口称重 */
    @Excel(name = "入口称重")
    private Long enWeight;

    /** 入口操作人员id */
    @Excel(name = "入口操作人员id")
    private String entryOperatorId;

    /** 出站时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "出站时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date exTime;

    /** 出口车道号编码 */
    @Excel(name = "出口车道号编码")
    private String exTollLaneId;

    /** 出口收费站编码 */
    @Excel(name = "出口收费站编码")
    private String exTollStationId;

    /** 出口收费站名称 */
    @Excel(name = "出口收费站名称")
    private String exTollStationName;

    /** 出口车种 */
    @Excel(name = "出口车种")
    private Integer exVehicleClass;

    /** 出口称重 */
    @Excel(name = "出口称重")
    private Long exWeight;

    /** 费用 */
    @Excel(name = "费用")
    private Long fee;

    /** 费显显示信息 */
    @Excel(name = "费显显示信息")
    private String feeBoardPlay;

    /** 收费里程 */
    @Excel(name = "收费里程")
    private Long feeMileage;

    /** 交易金额占比 */
    @Excel(name = "交易金额占比")
    private BigDecimal feeRate;

    /** 开票标识 */
    @Excel(name = "开票标识")
    private String identification;

    /** 车牌号+车牌类型 */
    @Excel(name = "车牌号+车牌类型")
    private String identifyVehicleId;

    /** 车道类型 */
    @Excel(name = "车道类型")
    private String laneType;

    /** 介质编码 */
    @Excel(name = "介质编码")
    private String mediaNo;

    /** 通行介质类型 */
    @Excel(name = "通行介质类型")
    private String mediaType;

    /** 标签无卡累计次数 */
    @Excel(name = "标签无卡累计次数")
    private Integer noCardCount;

    /** OBU序号编码 */
    @Excel(name = "OBU序号编码")
    private String obuId;

    /** OBU 单/双片标识 */
    @Excel(name = "OBU 单/双片标识")
    private String obuSign;

    /** 0BU 总累计交易金额 */
    @Excel(name = "0BU 总累计交易金额")
    private Long obuTotalAmount;

    /** OBU累计优惠后通行费金额 */
    @Excel(name = "OBU累计优惠后通行费金额")
    private Long obuTotalDiscountAmount;

    /** 操作id */
    @Excel(name = "操作id")
    private String operId;

    /** 参数 */
    @Excel(name = "参数")
    private String params;

    /** 通行id */
    @Excel(name = "通行id")
    private String passId;

    /** 支付id */
    @Excel(name = "支付id")
    private String paycardId;

    /** 应收金额 */
    @Excel(name = "应收金额")
    private Long payFee;

    /** 支付类型 */
    @Excel(name = "支付类型")
    private String payType;

    /** 本省金额 */
    @Excel(name = "本省金额")
    private Long provFee;

    /** 本省交易成功次数 */
    @Excel(name = "本省交易成功次数")
    private Integer provTransCount;

    /** 通行省份个数 */
    @Excel(name = "通行省份个数")
    private Integer provinceCount;

    /** 接收时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "接收时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date receiveTime;

    /** 工班号 */
    @Excel(name = "工班号")
    private String shift;

    /** 最短收费金额 */
    @Excel(name = "最短收费金额")
    private Long shortFee;

    /** 最短路径里程数 */
    @Excel(name = "最短路径里程数")
    private Long shortFeeMileage;

    /** 标记状态 */
    @Excel(name = "标记状态")
    private String signStatus;

    /** 全网最小费额费率版本号 */
    @Excel(name = "全网最小费额费率版本号")
    private Long spcrateVersion;

    /** 特殊类型 */
    @Excel(name = "特殊类型")
    private String specialType;

    /** 多条省内交易信息 */
    @Excel(name = "多条省内交易信息")
    private String splitProvince;

    /** TAC码 */
    @Excel(name = "TAC码")
    private String tac;

    /** 终端机编号 */
    @Excel(name = "终端机编号")
    private String terminalNo;

    /** PSAM卡脱机交易序列号 */
    @Excel(name = "PSAM卡脱机交易序列号")
    private String terminalTransNo;

    /** 卡面扣费金额 */
    @Excel(name = "卡面扣费金额")
    private Long transFee;

    /** 交易支付类型 */
    @Excel(name = "交易支付类型")
    private String transPaytype;

    /** 交易类型标识 */
    @Excel(name = "交易类型标识")
    private String transType;

    /** 车辆状态标识 */
    @Excel(name = "车辆状态标识")
    private String vehicleSign;

    /** 车牌识别流水号 */
    @Excel(name = "车牌识别流水号")
    private String vehicleSignId;

    /** 加载时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "加载时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date loadTime;

    /** 分类分级 */
    @Excel(name = "分类分级")
    private String gradeLevel;

    /** 备用字段1 */
    @Excel(name = "备用字段1")
    private String backCol1;

    /** 备用字段2 */
    @Excel(name = "备用字段2")
    private String backCol2;

    /** 状态（0正常1停用） */
    @Excel(name = "状态", readConverterExp = "0=正常1停用")
    private String status;

    /** 备注 */
    @Excel(name = "备注")
    private String remark;

}
