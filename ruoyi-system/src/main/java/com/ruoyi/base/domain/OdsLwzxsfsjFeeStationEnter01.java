package com.ruoyi.base.domain;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonFormat;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.Custom;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;

import java.math.BigDecimal;
import java.util.Date;

/**
 * 收费站入口数据对象 ods_lwzxsfsj_fee_station_enter_01
 *
 * @author ruoyi
 * @date 2025-09-18
 */
@Data
@TableName("ods_lwzxsfsj_fee_station_enter_01")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class OdsLwzxsfsjFeeStationEnter01 implements Custom {

    @TableId(value = "bigId", type = IdType.ASSIGN_UUID)
    private Long bigId;

    /**
     * CPC卡或ETC卡的编号
     */
    @Excel(name = "CPC卡或ETC卡的编号")
    private String cardid;

    /**
     * 单片式OBU/CPC卡电量百分比
     */
    @Excel(name = "单片式OBU/CPC卡电量百分比")
    private Long electricalpercentage;

    /**
     * 入站车轴数
     */
    @Excel(name = "入站车轴数")
    private Long enaxlecount;

    /**
     * 入站时间
     */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "入站时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date entime;

    /**
     * 入口车道hex
     */
    @Excel(name = "入口车道hex")
    private String entolllanehex;

    /**
     * 入口车道id
     */
    @Excel(name = "入口车道id")
    private String entolllaneid;

    /**
     * 入口收费站编码
     */
    @Excel(name = "入口收费站编码")
    private String entollstationid;

    /**
     * 入口称重
     */
    @Excel(name = "入口称重")
    private BigDecimal enweight;

    /**
     * 车牌号+车牌类型
     */
    @Excel(name = "车牌号+车牌类型")
    private String identifyvehicleid;

    /**
     * 车道类型
     */
    @Excel(name = "车道类型")
    private String lanetype;

    /**
     * 介质类型
     */
    @Excel(name = "介质类型")
    private String mediatype;

    /**
     * 操作id
     */
    @Excel(name = "操作id")
    private String operid;

    /**
     * 作业媒介
     */
    @Excel(name = "作业媒介")
    private String operationmedia;

    /**
     * 参数
     */
    @Excel(name = "参数")
    private String params;

    /**
     * 通行id
     */
    @Excel(name = "通行id")
    private String passid;

    /**
     * 接收时间
     */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "接收时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date receivetime;

    /**
     * 工班号
     */
    @Excel(name = "工班号")
    private String shift;

    /**
     * 标记状态
     */
    @Excel(name = "标记状态")
    private String signstatus;

    /**
     * 特殊类型
     */
    @Excel(name = "特殊类型")
    private String specialtype;

    /**
     * TAC码
     */
    @Excel(name = "TAC码")
    private String tac;

    /**
     * 终端机编号
     */
    @Excel(name = "终端机编号")
    private String terminalno;

    /**
     * PSAM卡脱机交易序列号
     */
    @Excel(name = "PSAM卡脱机交易序列号")
    private String terminaltransno;

    /**
     * 交易金额
     */
    @Excel(name = "交易金额")
    private BigDecimal transfee;

    /**
     * 交易类型
     */
    @Excel(name = "交易类型")
    private String transtype;

    /**
     * 总数
     */
    @Excel(name = "总数")
    private Long vcount;

    /**
     * 车种
     */
    @Excel(name = "车种")
    private String vehicleclass;

    /**
     * 车牌号+车牌类型
     */
    @Excel(name = "车牌号+车牌类型")
    private String vehicleid;

    /**
     * 车辆识别标识
     */
    @Excel(name = "车辆识别标识")
    private String vehiclesign;

    /**
     * 车牌识别流水号
     */
    @Excel(name = "车牌识别流水号")
    private String vehiclesignid;

    /**
     * 车辆类型
     */
    @Excel(name = "车辆类型")
    private String vehicletype;

    /**
     * 加载时间
     */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "加载时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date loadTime;

    /**
     * 分类分级
     */
    @Excel(name = "分类分级")
    private String gradeLevel;


}
