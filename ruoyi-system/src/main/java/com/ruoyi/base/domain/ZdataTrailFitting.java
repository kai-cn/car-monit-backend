package com.ruoyi.base.domain;

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
 * 车辆出入口拟合轨迹对象 zdata_trail_fitting
 *
 * @author ruoyi
 * @date 2025-10-15
 */
@Data
@TableName("zdata_trail_fitting")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class ZdataTrailFitting  implements Custom {

    /** 轨迹唯一标识（cid） */
    private String cid;

    /** 入口车轴数 */
    @Excel(name = "入口车轴数")
    private Integer enaxlecount;

    /** 入口时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "入口时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date entime;

    /** 入口车道编号 */
    @Excel(name = "入口车道编号")
    private String entolllaneid;

    /** 入口收费站编号 */
    @Excel(name = "入口收费站编号")
    private String entollstationid;

    /** 入口收费站名称 */
    @Excel(name = "入口收费站名称")
    private String entollstationname;

    /** 入口车型分类（收费车型） */
    @Excel(name = "入口车型分类", readConverterExp = "收=费车型")
    private Integer envehicleclass;

    /** 入口车辆编号 */
    @Excel(name = "入口车辆编号")
    private String envehicleid;

    /** 入口车辆类型代码 */
    @Excel(name = "入口车辆类型代码")
    private Integer envehicletype;

    /** 入口称重（kg） */
    @Excel(name = "入口称重", readConverterExp = "k=g")
    private Long enweight;

    /** 出口时间（分区键） */
    @Excel(name = "出口时间", readConverterExp = "分=区键")
    private Date extime;

    /** 出口车道编号 */
    @Excel(name = "出口车道编号")
    private String extolllaneid;

    /** 出口收费站编号 */
    @Excel(name = "出口收费站编号")
    private String extollstationid;

    /** 出口收费站名称 */
    @Excel(name = "出口收费站名称")
    private String extollstationname;

    /** 出口车型分类（收费车型） */
    @Excel(name = "出口车型分类", readConverterExp = "收=费车型")
    private Integer exvehicleclass;

    /** 出口车辆编号 */
    @Excel(name = "出口车辆编号")
    private String exvehicleid;

    /** 出口车辆类型代码 */
    @Excel(name = "出口车辆类型代码")
    private Integer exvehicletype;

    /** 出口称重（kg） */
    @Excel(name = "出口称重", readConverterExp = "k=g")
    private Long exweight;

    /** 拟合轨迹点集合 */
    @Excel(name = "拟合轨迹点集合")
    private String trailpoints;


}
