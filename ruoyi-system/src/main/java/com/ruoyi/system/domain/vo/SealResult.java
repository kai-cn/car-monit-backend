package com.ruoyi.system.domain.vo;

import com.fasterxml.jackson.annotation.JsonAlias;
import lombok.Data;

@Data
public class SealResult implements java.io.Serializable{

    private static final long serialVersionUID = -2717671591320235358L;
    @JsonAlias("ret_code")
    private int retCode = 0;
    @JsonAlias("ret_msg")
    private String retMsg = null;
    @JsonAlias("document_no")
    private String documentNo = null;
    private String pdf = null;
    private SealResultData data = null;



}
