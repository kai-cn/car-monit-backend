package com.ruoyi.base.domain;

import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonFormat;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BasePlusEntityNew;
import com.ruoyi.common.core.domain.Custom;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;

import java.math.BigDecimal;
import java.util.Date;

/**
 * 基础-收费流水对象 base_fee_records
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Data
@TableName("base_fee_records")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class BaseFeeRecords extends BasePlusEntityNew implements Custom {

    /** 主键 */
    private String bigId;

    /** 算法标识 */
    @Excel(name = "算法标识")
    private String algorithmIdentifier;

    /** 天线ID编号(天线头编号) */
    @Excel(name = "天线ID编号(天线头编号)")
    private String antennaId;

    /** 车轴数 */
    @Excel(name = "车轴数")
    private Long axleCount;

    /** 交易后余额 */
    @Excel(name = "交易后余额")
    private BigDecimal balanceAfter;

    /** 交易前余额 */
    @Excel(name = "交易前余额")
    private BigDecimal balanceBefore;

    /** 本次交易后卡片累计金额 */
    @Excel(name = "本次交易后卡片累计金额")
    private BigDecimal cardFeeSumAfter;

    /** 本次交易前卡片累计金额 */
    @Excel(name = "本次交易前卡片累计金额")
    private BigDecimal cardFeeSumBefore;

    /** 控制器序号 */
    @Excel(name = "控制器序号")
    private String computerOrder;

    /** 交易耗时（单位：ms） */
    @Excel(name = "交易耗时", readConverterExp = "单=位：ms")
    private Long consumeTime;

    /** CPU卡编号 */
    @Excel(name = "CPU卡编号")
    private String cpuCardId;

    /** CPU卡类型 */
    @Excel(name = "CPU卡类型")
    private String cpuCardType;

    /** CPU截止日期 */
    @Excel(name = "CPU截止日期")
    private String cpuEndDate;

    /** CPU卡片发行方标识 */
    @Excel(name = "CPU卡片发行方标识")
    private String cpuIssueId;

    /** CPU卡片网络编号 */
    @Excel(name = "CPU卡片网络编号")
    private String cpuNetId;

    /** CPU起始日期 */
    @Excel(name = "CPU起始日期")
    private String cpuStartDate;

    /** CPU 内车牌号码 */
    @Excel(name = "CPU 内车牌号码")
    private String cpuVehiclePlate;

    /** CPU内车型 */
    @Excel(name = "CPU内车型")
    private String cpuVehicleType;

    /** CPU用户卡版本号 */
    @Excel(name = "CPU用户卡版本号")
    private String cpuVersion;

    /** 处理状态 */
    @Excel(name = "处理状态")
    private String dealStatus;

    /** 优惠金额 */
    @Excel(name = "优惠金额")
    private BigDecimal discountFee;

    /** 优惠金额组合 */
    @Excel(name = "优惠金额组合")
    private String discountFeeGroup;

    /** 入口车道类型 */
    @Excel(name = "入口车道类型")
    private String enLaneType;

    /** 进站时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "进站时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date enTime;

    /** 进站收费站车道号 */
    @Excel(name = "进站收费站车道号")
    private String enTollLaneId;

    /** 进站收费站hex编码 */
    @Excel(name = "进站收费站hex编码")
    private String enTollStationHex;

    /** 费用 */
    @Excel(name = "费用")
    private BigDecimal fee;

    /** 计费模块响应计费结果 */
    @Excel(name = "计费模块响应计费结果")
    private String feeCalcResult;

    /** 计费接口特情值 */
    @Excel(name = "计费接口特情值")
    private String feeCalcSpecial;

    /** 计费特情值组合 */
    @Excel(name = "计费特情值组合")
    private String feeCalcSpecials;

    /** 交易金额组合 */
    @Excel(name = "交易金额组合")
    private String feeGroup;

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
    private BigDecimal feeMileage;

    /** 本省计费起点 */
    @Excel(name = "本省计费起点")
    private String feeProvBeginHex;

    /** 计费协议保留字段1 */
    @Excel(name = "计费协议保留字段1")
    private String feespare1;

    /** 计费协议保留字段2 */
    @Excel(name = "计费协议保留字段2")
    private String feespare2;

    /** 计费车型 */
    @Excel(name = "计费车型")
    private String feeVehicleType;

    /** 门架Hex值 */
    @Excel(name = "门架Hex值")
    private String gantryHex;

    /** 对向门架Hex值 */
    @Excel(name = "对向门架Hex值")
    private String gantryHexOpposite;

    /** 门架编码 */
    @Excel(name = "门架编码")
    private String gantryId;

    /** 门架顺序号 */
    @Excel(name = "门架顺序号")
    private Long gantryOrderNum;

    /** 门架类型 */
    @Excel(name = "门架类型")
    private String gantryType;

    /** 节假日状态 */
    @Excel(name = "节假日状态")
    private String holidayState;

    /** 小时批次号 */
    @Excel(name = "小时批次号")
    private String hourBatchNo;

    /** 消费密钥版本号 */
    @Excel(name = "消费密钥版本号")
    private String keyVersion;

    /** 上一个门架的hex编号 */
    @Excel(name = "上一个门架的hex编号")
    private String lastGantryHex;

    /** 通过上一个门架的时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "通过上一个门架的时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date lastGantryTime;

    /** 匹配状态 */
    @Excel(name = "匹配状态")
    private String matchstatus;

    /** 通行介质类型 */
    @Excel(name = "通行介质类型")
    private String mediaType;

    /** 本次交易后累计无卡次数 */
    @Excel(name = "本次交易后累计无卡次数")
    private Long noCardTimesAfter;

    /** 本次交易前累计无卡次数 */
    @Excel(name = "本次交易前累计无卡次数")
    private Long noCardtimesBefore;

    /** OBU/CPC卡电量百分比 */
    @Excel(name = "OBU/CPC卡电量百分比")
    private Long obuElectrical;

    /** OBU/CPC截止日期 */
    @Excel(name = "OBU/CPC截止日期")
    private String obuEndDate;

    /** 本次交易后标签累计实收金额 */
    @Excel(name = "本次交易后标签累计实收金额")
    private BigDecimal obuFeeSumAfter;

    /** 本次交易前标签累计实收金额 */
    @Excel(name = "本次交易前标签累计实收金额")
    private BigDecimal obuFeeSumBefore;

    /** 读取标签入口信息类型 */
    @Excel(name = "读取标签入口信息类型")
    private String obuInfoTypeRead;

    /** 本次写入标签入口信息类型 */
    @Excel(name = "本次写入标签入口信息类型")
    private String obuInfoTypeWrite;

    /** OBU/CPC发行方标识 */
    @Excel(name = "OBU/CPC发行方标识")
    private String obuIssueId;

    /** OBU中上一个门架HEX */
    @Excel(name = "OBU中上一个门架HEX")
    private String obuLastGantryHex;

    /** OBU中通过上一个门架时间 */
    @Excel(name = "OBU中通过上一个门架时间")
    private String obuLastGantryTime;

    /** OBU /CPC物理地址 */
    @Excel(name = "OBU /CPC物理地址")
    private String obuMac;

    /** 本次交易后标签累计里程 */
    @Excel(name = "本次交易后标签累计里程")
    private BigDecimal obuMileageAfter;

    /** 本次交易前标签累计里程 */
    @Excel(name = "本次交易前标签累计里程")
    private BigDecimal obuMileageBefore;

    /** 标签入口状态 */
    @Excel(name = "标签入口状态")
    private String obuPassState;

    /** 本次交易后标签累计应收金额 */
    @Excel(name = "本次交易后标签累计应收金额")
    private String obuPayFeeSumAfter;

    /** 本次交易前标签累计应收金额 */
    @Excel(name = "本次交易前标签累计应收金额")
    private String obuPayFeeSumBefore;

    /** 本次交易后标签累计金额（省内） */
    @Excel(name = "本次交易后标签累计金额", readConverterExp = "省=内")
    private String obuProvFeeSumAfter;

    /** 本次交易前标签累计金额 （省内） */
    @Excel(name = "本次交易前标签累计金额 ", readConverterExp = "省=内")
    private String obuProvFeeSumBefore;

    /** 本次交易后标签累计应收金额（省内） */
    @Excel(name = "本次交易后标签累计应收金额", readConverterExp = "省=内")
    private String obuProvPayFeeSumAfter;

    /** 本次交易前标签累计应收金额（省内） */
    @Excel(name = "本次交易前标签累计应收金额", readConverterExp = "省=内")
    private String obuProvPayFeeSumBefore;

    /** 省内本次交易后标签累计写入成功数量 */
    @Excel(name = "省内本次交易后标签累计写入成功数量")
    private Long obuProvTradeSuccNumAfter;

    /** 省内本次交易前标签累计写入成功数量 */
    @Excel(name = "省内本次交易前标签累计写入成功数量")
    private Long obuProvTradeSuccNumBefore;

    /** OBU 单/双片标识 */
    @Excel(name = "OBU 单/双片标识")
    private String obuSign;

    /** OBU/CPC序号编码 */
    @Excel(name = "OBU/CPC序号编码")
    private String obusn;

    /** OBU/CPC起始日期 */
    @Excel(name = "OBU/CPC起始日期")
    private String obuStartDate;

    /** OBU/CPC状态 */
    @Excel(name = "OBU/CPC状态")
    private String obuState;

    /** 本次交易后标签累计写入成功总量 */
    @Excel(name = "本次交易后标签累计写入成功总量")
    private Long obuTotalTradeSuccNumAfter;

    /** 本次交易前标签累计写入成功总量 */
    @Excel(name = "本次交易前标签累计写入成功总量")
    private Long obuTotalTradeSuccNumBefore;

    /** 标签写入结果 */
    @Excel(name = "标签写入结果")
    private String obuTradeResult;

    /** obu车牌 */
    @Excel(name = "obu车牌")
    private String obuVehiclePlate;

    /** obu车牌类型 */
    @Excel(name = "obu车牌类型")
    private String obuVehicleType;

    /** OBU/CPC版本号 */
    @Excel(name = "OBU/CPC版本号")
    private String obuVersion;

    /** 参数 */
    @Excel(name = "参数")
    private String params;

    /** 通行id */
    @Excel(name = "通行id")
    private String passId;

    /** 通行状态 */
    @Excel(name = "通行状态")
    private String passState;

    /** 本次计费拟合结果标识 */
    @Excel(name = "本次计费拟合结果标识")
    private String pathFitFlag;

    /** 应收金额 */
    @Excel(name = "应收金额")
    private String payFee;

    /** 应收金额组合 */
    @Excel(name = "应收金额组合")
    private String payFeeGroup;

    /** PC-RSU接口协议版本号 */
    @Excel(name = "PC-RSU接口协议版本号")
    private String pcrSuversion;

    /** 本省累计通行金额参考 */
    @Excel(name = "本省累计通行金额参考")
    private BigDecimal provminfee;

    /** 本次交易后累计省份数量 */
    @Excel(name = "本次交易后累计省份数量")
    private Long provinceNumAfter;

    /** 本次交易前累计省份数量 */
    @Excel(name = "本次交易前累计省份数量")
    private Long provinceNumBefore;

    /** 计费模块计费模式 */
    @Excel(name = "计费模块计费模式")
    private String rateCompute;

    /** 计费模块拟合点总数 */
    @Excel(name = "计费模块拟合点总数")
    private Long rateFitCount;

    /** 计费模块和计费参数版本号 */
    @Excel(name = "计费模块和计费参数版本号")
    private String rateVersion;

    /** 本次交易读取的EF04加密摘要验证结果 */
    @Excel(name = "本次交易读取的EF04加密摘要验证结果")
    private String readCipherTextVerify;

    /** 接收时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "接收时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date receiveTime;

    /** 交易的服务类型 */
    @Excel(name = "交易的服务类型")
    private String serviceType;

    /** 门架后台入库时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "门架后台入库时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date stationDbtime;

    /** 门架后台处理时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "门架后台处理时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date stationDealTime;

    /** 门架后台匹配时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "门架后台匹配时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date stationMatchTime;

    /** 门架后台去重时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "门架后台去重时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date stationValidTime;

    /** TAC码 */
    @Excel(name = "TAC码")
    private String tac;

    /** 终端机编号 */
    @Excel(name = "终端机编号")
    private String terminalNo;

    /** PSAM卡脱机交易序列号 */
    @Excel(name = "PSAM卡脱机交易序列号")
    private String terminalTransNo;

    /** 收费单元编号组合 */
    @Excel(name = "收费单元编号组合")
    private String tollIntervalId;

    /** 收费单元处理标识 */
    @Excel(name = "收费单元处理标识")
    private String tollIntervalSign;

    /** 车货总重 */
    @Excel(name = "车货总重")
    private String totalWeight;

    /** 计费交易编号 */
    @Excel(name = "计费交易编号")
    private String tradeId;

    /** 本次交易读取的EF04加密摘要 */
    @Excel(name = "本次交易读取的EF04加密摘要")
    private String tradeReadCipherText;

    /** 卡片复合交易结果 */
    @Excel(name = "卡片复合交易结果")
    private String traderResult;

    /** 交易类型 */
    @Excel(name = "交易类型")
    private String tradeType;

    /** 本次交易生成的EF04加密摘要 */
    @Excel(name = "本次交易生成的EF04加密摘要")
    private String tradeWriteCipherText;

    /** 卡面扣费金额 */
    @Excel(name = "卡面扣费金额")
    private BigDecimal transFee;

    /** IC卡交易序号 */
    @Excel(name = "IC卡交易序号")
    private String transNo;

    /** 计费交易时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "计费交易时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date transTime;

    /** 交易类型标识 */
    @Excel(name = "交易类型标识")
    private String transType;

    /** 去重状态 */
    @Excel(name = "去重状态")
    private String validStatus;

    /** 车种 */
    @Excel(name = "车种")
    private String vehicleClass;

    /** 车高 */
    @Excel(name = "车高")
    private BigDecimal vehicleHight;

    /** 车长 */
    @Excel(name = "车长")
    private BigDecimal vehicleLength;

    /** 车牌号+类型 */
    @Excel(name = "车牌号+类型")
    private String vehiclePlate;

    /** 车辆座位数/载重 */
    @Excel(name = "车辆座位数/载重")
    private String vehicleSeat;

    /** 车辆状态标识 */
    @Excel(name = "车辆状态标识")
    private String vehicleSign;

    /** 车辆类型 */
    @Excel(name = "车辆类型")
    private String vehicleType;

    /** 车辆用户类型 */
    @Excel(name = "车辆用户类型")
    private String vehicleUserType;

    /** 车宽 */
    @Excel(name = "车宽")
    private BigDecimal vehicleWidth;

    /** 校验码 */
    @Excel(name = "校验码")
    private String verifyCode;

    /** 加载时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "加载时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date loadTime;

    /** 分类分级 */
    @Excel(name = "分类分级")
    private Long gradeLevel;

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
