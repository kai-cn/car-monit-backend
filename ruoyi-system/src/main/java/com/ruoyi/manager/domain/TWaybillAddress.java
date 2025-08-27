//package com.ruoyi.manager.domain;
//
//import com.baomidou.mybatisplus.annotation.IdType;
//import com.baomidou.mybatisplus.annotation.TableField;
//import com.baomidou.mybatisplus.annotation.TableId;
//import com.baomidou.mybatisplus.annotation.TableName;
//import com.ruoyi.common.annotation.NullDefault;
//import lombok.Builder;
//import lombok.Data;
//import lombok.EqualsAndHashCode;
//
//import java.math.BigDecimal;
//
//@Data
//@EqualsAndHashCode(callSuper = false)
//@TableName("t_waybill_address")
//@Builder
//public class TWaybillAddress {
//    private static final long serialVersionUID = 1L;
//
//    /** 主键 */
//    @TableId(value = "id", type = IdType.ASSIGN_ID)
//    private String id;
//
//    /** 运单id */
//    private String waybillId;
//
//    /** 位置类型：1 门地址 2 港口码头 */
//    private String posType;
//
//    /** 1 发货地址 2 收货地址 */
//    private String type;
//    @NullDefault
//    /** 姓名 */
//    private String name;
//    @NullDefault
//    /** 联系电话 */
//    private String phone;
//    @NullDefault
//    /** 行政区划代码 */
//    private String areacode;
//    @NullDefault
//    /** 经度 GCJ-02 */
//    private BigDecimal longitude;
//    @NullDefault
//    /** 纬度 GCJ-02 */
//    private BigDecimal latitude;
//    @NullDefault
//    /** 地址 */
//    private String address;
//    @NullDefault
//    /** 详细地址 */
//    @TableField("addrDetail")
//    private String addrDetail;
//    /** 港区id */
//    @NullDefault
//    @TableField("portId")
//    private String portId;
//    @NullDefault
//    /** 港区名称 */
//    @TableField("portName")
//    private String portName;
//    @NullDefault
//    /** 码头id */
//    @TableField("wharfId")
//    private String wharfId;
//    @NullDefault
//    /** 码头名称 */
//    @TableField("wharfName")
//    private String wharfName;
//}
