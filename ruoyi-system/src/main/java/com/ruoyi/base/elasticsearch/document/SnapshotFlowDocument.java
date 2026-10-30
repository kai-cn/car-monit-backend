package com.ruoyi.base.elasticsearch.document;

import lombok.Data;

import java.io.Serializable;
import java.math.BigDecimal;
import java.util.Date;

@Data
public class SnapshotFlowDocument implements Serializable {

    private static final long serialVersionUID = 1L;

    private String bigId;

    private String datasource;

    private String cameratype;

    private String deviceid;

    private String gantrycode;

    private String gantryname;

    private String roadcode;

    private String roadname;

    private String sectioncode;

    private String sectionname;

    private String tollcode;

    private String tollname;

    private String orgcode;

    private String orgname;

    private Integer direction;

    private String hexcode;

    private String pileno;

    private BigDecimal lon;

    private BigDecimal lat;

    private String deviceip;

    private Long siteid;

    private Integer laneid;

    private Long snapshottimeunix;

    private Date snapshottime;

    private Long receivedtimeunix;

    private Date receivedtime;

    private String platenumber;

    private String platecolor;

    private Integer platecolorcode;

    private String platetype;

    private Integer platetypecode;

    private Integer plateconfidence;

    private String carbrand;

    private String carcolor;

    private Integer carcolorcode;

    private String cartype;

    private Integer cartypecode;

    private String cardirection;

    private String snappicturepath;

    private Date loadtime;

    private Integer gradelevel;

    private String datauuid;

    private String reserve3;
}
