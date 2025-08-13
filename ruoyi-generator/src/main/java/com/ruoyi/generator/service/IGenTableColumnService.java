package com.ruoyi.generator.service;

import com.ruoyi.generator.domain.GenTableColumn;

import java.util.List;

/**
 * 业务字段 服务层
 * 
 * @author ruoyi
 */
public interface IGenTableColumnService
{
    /**
     * 查询业务字段列表
     * 
     * @param tableId 业务字段编号
     * @return 业务字段集合
     */
    public List<GenTableColumn> selectGenTableColumnListByTableId(Long tableId);

    /**
     * 根据ids查询对应的信息
     * @param tableColumnIds
     * @return
     */
    List<GenTableColumn> selectGenTableColumnListByTableColumnIds(String tableColumnIds);

    /**
     * 根据id列表查询对应的信息
     * @param tableColumnIdList
     * @return
     */
    List<GenTableColumn> selectGenTableColumnListByTableColumnIdList(List<Long> tableColumnIdList);

    /**
     * 查询字段信息
     * @param genTableColumn
     * @return
     */
    List<GenTableColumn> selectGenTableColumnList(GenTableColumn genTableColumn);

    /**
     * 新增业务字段
     * 
     * @param genTableColumn 业务字段信息
     * @return 结果
     */
    public int insertGenTableColumn(GenTableColumn genTableColumn);

    /**
     * 修改业务字段
     * 
     * @param genTableColumn 业务字段信息
     * @return 结果
     */
    public int updateGenTableColumn(GenTableColumn genTableColumn);

    /**
     * 删除业务字段信息
     * 
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    public int deleteGenTableColumnByIds(String ids);
}
