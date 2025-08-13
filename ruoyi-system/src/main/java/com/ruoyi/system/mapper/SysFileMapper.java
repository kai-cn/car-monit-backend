package com.ruoyi.system.mapper;

import com.ruoyi.system.domain.SysFile;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * 文件管理Mapper接口
 *
 * @author ruoyi
 * @date 2021-07-29
 */
@Repository
public interface SysFileMapper {
    /**
     * 查询文件管理
     *
     * @param ids 文件管理ID
     * @return 文件管理
     */
    public List<SysFile> selectSysFileByIds(String[] ids);

    public SysFile selectSysFileById(Long id);

    /**
     * 查询文件管理列表
     *
     * @param sysFile 文件管理
     * @return 文件管理集合
     */
    public List<SysFile> selectSysFileList(SysFile sysFile);

    /**
     * 新增文件管理
     *
     * @param sysFile 文件管理
     * @return 结果
     */
    public int insertSysFile(SysFile sysFile);

    /**
     * 修改文件管理
     *
     * @param sysFile 文件管理
     * @return 结果
     */
    public int updateSysFile(SysFile sysFile);

    /**
     * 删除文件管理
     *
     * @param id 文件管理ID
     * @return 结果
     */
    public int deleteSysFileById(Long id);

    /**
     * 批量删除文件管理
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    public int deleteSysFileByIds(Long[] ids);


    /**
     * 删除文件管理
     *
     * @param id 文件管理ID
     * @return 结果
     */
    public int deleteSysFileByIdNew(Long id);

    /**
     * 更新CA驱动程序的ID
     * @param sysFile
     * @return
     */
    public int updateCAFile(SysFile sysFile);
}
