package com.ruoyi.base.domain;

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
 * 收费站基础信息对象 ods_szdn_toll
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@Data
@TableName("ods_szdn_toll")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class OdsSzdnToll implements Custom {

    @TableId(value = "id", type = IdType.ASSIGN_UUID)
    private String id;

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


}
