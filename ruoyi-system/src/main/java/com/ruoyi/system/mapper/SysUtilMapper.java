package com.ruoyi.system.mapper;

import com.ruoyi.system.domain.SysUtil;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * 参数配置 数据层
 * 
 * @author ruoyi
 */
@Repository
public interface SysUtilMapper
{
    /**
     * 根据业务查询编码
     *
     * @param bo
     * @return
     */
    SysUtil getBussCode(SysUtil bo);
}
