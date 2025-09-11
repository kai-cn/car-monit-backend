package com.ruoyi.manager.domain.vo.bigscreen;


import lombok.Data;

/**
 * @Author: zhukai
 * @Date: 2025/08/28/15:00
 * @Description:
 */
@Data
public class CarLocationParam {

    /**
     * 所属管理中心机构编码
     */
    private String orgCode;

    /**
     * 门架编号
     */
    private String gantryCode;

    /**
     * 所属路线编码
     */
    private String roadCode;

//    @ApiModelProperty("所属路线名称")
//    private String roadName;
//
//    @ApiModelProperty("所属收费站名称")
//    private String tollName;

//    @ApiModelProperty("路段id")
//    private String roadSectionId;

    /**
     * 所属路段编码
     */
    private String sectionCode;

    /**
     * 所属收费站编码
     */
    private String tollCode;

    /**
     * 逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂
     */
    private String escapedType;

    /**
     * 服务区编码
     */
    private String fwqbm;

    /**
     * 1收费站、2门架、3服务区
     */
    private String type;

    /**
     * 编码
     */
    private String code;

    /**
     * 车牌号
     */
    private String carNoQuery;


}
