package com.ruoyi.base.domain;

import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Data
public class SuspiciousCarVO {

    /**
     * 签名key
     */
    private String signatureKey;

    /**
     * 时间戳
     */
    private Long timeStamp;

    /**
     * 签名
     * @see
     */
    private String signature;

    List<TrailInfo> trailInfoList = new ArrayList<>();


}
