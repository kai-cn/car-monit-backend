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

import java.util.Date;

/**
 * 省界抓拍对象 ods_rt_szdn_snapshot_flow_provcapture_addcode
 *
 * @author ruoyi
 * @date 2025-09-18
 */
@Data
@TableName("ods_rt_szdn_snapshot_flow_provcapture_addcode")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class OdsRtSzdnSnapshotFlowProvcaptureAddcode implements Custom {

    @TableId(value = "bigId", type = IdType.ASSIGN_UUID)
    private Long bigId;

    private String deviceip;

    private Long tailcapturetimeunix;

    private Date tailcapturetime;

    private String extendattribute;

    private Integer smallsideimagewidth;

    private String axletype;

    /**
     * 小侧图高度
     */
    @Excel(name = "小侧图高度")
    private Integer smallsideimageheight;

    /**
     * 车牌颜色编码
     */
    @Excel(name = "车牌颜色编码")
    private Integer platecolorcode;

    /**
     * 车牌颜色
     */
    @Excel(name = "车牌颜色")
    private String platecolor;

    /** 车牌颜色名称（sys_dict_data plate_color 字典 label） */
    @Excel(name = "车牌颜色名称")
    @com.baomidou.mybatisplus.annotation.TableField(exist = false)
    private String plateColorName;

    /** 字典标记：UNKNOWN=字典未命中，已回退原始码 */
    @com.baomidou.mybatisplus.annotation.TableField(exist = false)
    private String plateColorMark;

    /**
     * 遮挡信息
     */
    @Excel(name = "遮挡信息")
    private String cover;

    /**
     * 平均可信度
     */
    @Excel(name = "平均可信度")
    private Integer averageauthoritative;

    /**
     * 车头车道号
     */
    @Excel(name = "车头车道号")
    private Integer headlanecode;

    /**
     * 特殊车辆标识
     */
    @Excel(name = "特殊车辆标识")
    private Integer specialvehicle;

    /**
     * 车长
     */
    @Excel(name = "车长")
    private Integer carlength;

    /**
     * 结果类型
     */
    @Excel(name = "结果类型")
    private String resulttype;

    /**
     * 车高
     */
    @Excel(name = "车高")
    private Integer carhight;

    /**
     * 车型编码
     */
    @Excel(name = "车型编码")
    private Integer carmodelscode;

    /**
     * 车型
     */
    @Excel(name = "车型")
    private String carmodels;

    /**
     * 车道位置
     */
    @Excel(name = "车道位置")
    private String laneposition;

    /**
     * 首字可信度
     */
    @Excel(name = "首字可信度")
    private Integer firstauthoritative;

    /**
     * 车尾车牌图高度
     */
    @Excel(name = "车尾车牌图高度")
    private Integer tailplateimageheight;

    /**
     * 车轴数
     */
    @Excel(name = "车轴数")
    private Integer axlecount;

    /**
     * 车牌图宽度
     */
    @Excel(name = "车牌图宽度")
    private Integer plateimagewidth;

    /**
     * 特殊类别
     */
    @Excel(name = "特殊类别")
    private String specialclass;

    /**
     * 车尾车牌号
     */
    @Excel(name = "车尾车牌号")
    private String tailplatenumber;

    /**
     * 车尾图路径
     */
    @Excel(name = "车尾图路径")
    private String tailimage;

    /**
     * 车身图采集时间(Unix时间戳)
     */
    @Excel(name = "车身图采集时间(Unix时间戳)")
    private Long sidecapturetimeunix;

    /**
     * 车身图采集时间(可读格式)
     */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "车身图采集时间(可读格式)", width = 30, dateFormat = "yyyy-MM-dd")
    private Date sidecapturetime;

    /**
     * 车身车道号
     */
    @Excel(name = "车身车道号")
    private Integer sidelanecode;

    /**
     * 轴距
     */
    @Excel(name = "轴距")
    private Integer wheelbase;

    /**
     * 附加信息
     */
    @Excel(name = "附加信息")
    private String attached;

    /**
     * 车轮数量
     */
    @Excel(name = "车轮数量")
    private Integer wheelcount;

    /**
     * 全局唯一标识符
     */
    @Excel(name = "全局唯一标识符")
    private String guid;

    /**
     * 车身图宽度
     */
    @Excel(name = "车身图宽度")
    private Integer sideimagewidth;

    /**
     * 车牌图高度
     */
    @Excel(name = "车牌图高度")
    private Integer plateimageheight;

    /**
     * 数据来源
     */
    @Excel(name = "数据来源")
    private String datasource;

    /**
     * 车辆分类
     */
    @Excel(name = "车辆分类")
    private String carclass;

    /**
     * 门架编号
     */
    @Excel(name = "门架编号")
    private String gantryid;

    /**
     * 小侧图路径
     */
    @Excel(name = "小侧图路径")
    private String smallsideimage;

    /**
     * 车头图高度
     */
    @Excel(name = "车头图高度")
    private Integer headimageheight;

    /**
     * 车侧拍摄场景编码
     */
    @Excel(name = "车侧拍摄场景编码")
    private Integer sidescenetypecode;

    /**
     * 车侧拍摄场景
     */
    @Excel(name = "车侧拍摄场景")
    private String sidescenetype;

    /**
     * 车尾图宽度
     */
    @Excel(name = "车尾图宽度")
    private Integer tailimagewidth;

    /**
     * 环境状态
     */
    @Excel(name = "环境状态")
    private String envstate;

    /**
     * 车头拍摄场景编码
     */
    @Excel(name = "车头拍摄场景编码")
    private Integer headscenetypecode;

    /**
     * 车头拍摄场景
     */
    @Excel(name = "车头拍摄场景")
    private String headscenetype;

    /**
     * 车侧行驶方向编码
     */
    @Excel(name = "车侧行驶方向编码")
    private Integer sidedrivingdirectioncode;

    /**
     * 车侧行驶方向
     */
    @Excel(name = "车侧行驶方向")
    private String sidedrivingdirection;

    /**
     * 车身图高度
     */
    @Excel(name = "车身图高度")
    private Integer sideimageheight;

    /**
     * 车速
     */
    @Excel(name = "车速")
    private String speed;

    /**
     * 车尾车牌图路径
     */
    @Excel(name = "车尾车牌图路径")
    private String tailplateimage;

    /**
     * 车头行驶方向编码
     */
    @Excel(name = "车头行驶方向编码")
    private Integer headdrivingdirectioncode;

    /**
     * 车头行驶方向
     */
    @Excel(name = "车头行驶方向")
    private String headdrivingdirection;

    /**
     * 车辆类型
     */
    @Excel(name = "车辆类型")
    private String cartype;

    /**
     * 车牌图路径
     */
    @Excel(name = "车牌图路径")
    private String plateimage;

    /**
     * 变道信息
     */
    @Excel(name = "变道信息")
    private String changelane;

    /**
     * 车身图路径
     */
    @Excel(name = "车身图路径")
    private String sideimage;

    /**
     * 车尾车牌位置
     */
    @Excel(name = "车尾车牌位置")
    private String tailplateposition;

    /**
     * 车头图宽度
     */
    @Excel(name = "车头图宽度")
    private Integer headimagewidth;

    /**
     * 车头图路径
     */
    @Excel(name = "车头图路径")
    private String headimage;

    /**
     * 车重
     */
    @Excel(name = "车重")
    private Integer carweight;

    /**
     * 车尾图高度
     */
    @Excel(name = "车尾图高度")
    private Integer tailimageheight;

    /**
     * 设备编号
     */
    @Excel(name = "设备编号")
    private String devicecode;

    /**
     * 车牌号码
     */
    @Excel(name = "车牌号码")
    private String platenumber;

    /**
     * 车尾车牌颜色编码
     */
    @Excel(name = "车尾车牌颜色编码")
    private Integer tailplatecolorcode;

    /**
     * 车尾车牌颜色
     */
    @Excel(name = "车尾车牌颜色")
    private String tailplatecolor;

    /**
     * 上传时间(Unix时间戳)
     */
    @Excel(name = "上传时间(Unix时间戳)")
    private Long uploadtimeunix;

    /**
     * 上传时间(可读格式)
     */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "上传时间(可读格式)", width = 30, dateFormat = "yyyy-MM-dd")
    private Date uploadtime;

    /**
     * 假轴数
     */
    @Excel(name = "假轴数")
    private Integer impostoraxlecount;

    /**
     * 车尾车道号
     */
    @Excel(name = "车尾车道号")
    private Integer taillanecode;

    /**
     * 站点ID
     */
    @Excel(name = "站点ID")
    private Integer siteid;

    /**
     * 车头图采集时间(Unix时间戳)
     */
    @Excel(name = "车头图采集时间(Unix时间戳)")
    private Long headcapturetimeunix;

    /**
     * 车头图采集时间(可读格式)
     */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "车头图采集时间(可读格式)", width = 30, dateFormat = "yyyy-MM-dd")
    private Date headcapturetime;

    /**
     * 车牌位置
     */
    @Excel(name = "车牌位置")
    private String plateposition;

    /**
     * 车尾车牌图宽度
     */
    @Excel(name = "车尾车牌图宽度")
    private Integer tailplateimagewidth;

    private Date loadtime;

    private Integer gradelevel;

    private String datauuid;

    private String reserve1;

    private String reserve2;

    private String reserve3;


}
