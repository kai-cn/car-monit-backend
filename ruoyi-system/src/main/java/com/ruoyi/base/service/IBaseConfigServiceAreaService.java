package com.ruoyi.base.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.base.domain.BaseConfigServiceArea;
import java.util.List;
import com.baomidou.mybatisplus.spring.service.IService;

/**
 * 服务区Service接口
 *
 * @author ruoyi
 * @date 2026-02-02
 */
public interface IBaseConfigServiceAreaService extends IService<BaseConfigServiceArea> {
    /**
     * 查询服务区
     *
     * @param fwqbm 服务区ID
     * @return 服务区
     */
    BaseConfigServiceArea selectBaseConfigServiceAreaById(String fwqbm);

    /**
     * 查询服务区列表
     *
     * @param baseConfigServiceArea 服务区
     * @return 服务区集合
     */
    List<BaseConfigServiceArea> selectBaseConfigServiceAreaList(BaseConfigServiceArea baseConfigServiceArea);


    /**
     * 新增或者修改服务区
     *
     * @param baseConfigServiceArea 服务区
     * @return 结果
     */
    AjaxResult saveBaseConfigServiceArea(BaseConfigServiceArea baseConfigServiceArea);

    /**
     * 批量删除服务区
     *
     * @param fwqbms 需要删除的服务区ID
     * @return 结果
     */
    AjaxResult deleteBaseConfigServiceAreaByIds(String[] fwqbms);

}
