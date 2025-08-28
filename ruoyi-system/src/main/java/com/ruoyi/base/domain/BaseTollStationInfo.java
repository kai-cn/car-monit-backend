package com.ruoyi.base.domain;

import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonFormat;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BasePlusEntityNew;
import com.ruoyi.common.core.domain.Custom;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;

import java.util.Date;

/**
 * 收费站基础信息对象 base_toll_station_info
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Data
@TableName("base_toll_station_info")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class BaseTollStationInfo extends BasePlusEntityNew implements Custom {

    /** 路线编号 */
    @Excel(name = "路线编号")
    private String roadCode;

    /** 收费站业务唯一编码 */
    @Excel(name = "收费站业务唯一编码")
    private String idCard;

    /** 收费站编号（内部） */
    @Excel(name = "收费站编号", readConverterExp = "内=部")
    private String tollCode;

    /** 收费站名称（内部） */
    @Excel(name = "收费站名称", readConverterExp = "内=部")
    private String tollName;

    /** 桩号 */
    @Excel(name = "桩号")
    private String pileNo;

    /** 所属机构名称 */
    @Excel(name = "所属机构名称")
    private String orgName;

    /** 收费站HEX编码 */
    @Excel(name = "收费站HEX编码")
    private String hexCode;

    /** 国网编号（内部） */
    @Excel(name = "国网编号", readConverterExp = "内=部")
    private String stateCode;

    /** 机构编码 */
    @Excel(name = "机构编码")
    private String orgCode;

    /** 经度 */
    @Excel(name = "经度")
    private String longitude;

    /** 纬度 */
    @Excel(name = "纬度")
    private String latitude;

    /** 开通日期 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "开通日期", width = 30, dateFormat = "yyyy-MM-dd")
    private Date openDate;

    /** 收费站别名 */
    @Excel(name = "收费站别名")
    private String tollAliasName;

    /** 入口治超监控资源，多个以英文逗号分割 */
    @Excel(name = "入口治超监控资源，多个以英文逗号分割")
    private String inMonitorResource;

    /** 车道抓拍监控资源，多个以英文逗号分割 */
    @Excel(name = "车道抓拍监控资源，多个以英文逗号分割")
    private String laneMonitorResource;

    /** 广场监控资源，多个以英文逗号分割 */
    @Excel(name = "广场监控资源，多个以英文逗号分割")
    private String squareMonitorResource;

    /** 动环监控资源，多个以英文逗号分割 */
    @Excel(name = "动环监控资源，多个以英文逗号分割")
    private String dynamicMonitorResource;

    /** 收费站编号 */
    @Excel(name = "收费站编号")
    private String tollCodeMerge;

    /** 国网编号 */
    @Excel(name = "国网编号")
    private String stateCodeMerge;

    /** 收费站名称 */
    @Excel(name = "收费站名称")
    private String tollNameMerge;

    /** 所属路段编码 */
    @Excel(name = "所属路段编码")
    private String sectionCode;

    /** 收费站对应机构编码 */
    @Excel(name = "收费站对应机构编码")
    private String tollOrgCode;

    /** 流水是否接入 */
    @Excel(name = "流水是否接入")
    private String isAccess;

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
