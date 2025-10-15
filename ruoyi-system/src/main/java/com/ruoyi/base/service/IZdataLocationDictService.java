package com.ruoyi.base.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.base.domain.ZdataLocationDict;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 车辆位置Service接口
 *
 * @author ruoyi
 * @date 2025-10-15
 */
public interface IZdataLocationDictService extends IService<ZdataLocationDict> {
    /**
     * 查询车辆位置
     *
     * @param id 车辆位置ID
     * @return 车辆位置
     */
    ZdataLocationDict selectZdataLocationDictById(Long id);

    /**
     * 查询车辆位置列表
     *
     * @param zdataLocationDict 车辆位置
     * @return 车辆位置集合
     */
    List<ZdataLocationDict> selectZdataLocationDictList(ZdataLocationDict zdataLocationDict);




}
