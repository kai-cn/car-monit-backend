package com.ruoyi.manager.domain.vo.bigscreen;

import lombok.Data;

/**
 * @Author: zhukai
 * @Date: 2025/08/28/15:00
 * @Description:
 */
@Data
public class TollGantryFwqVO {

    /**
     * 1收费站、2门架、3服务区
     */
    private String type;

    /**
     * 编码
     */
    private String code;

    /**
     * 名称
     */
    private String name;

}
