package com.ruoyi.system.service;

import com.amazonaws.services.s3.AmazonS3;
import com.amazonaws.services.s3.model.S3Object;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.system.domain.SysFile;
import com.ruoyi.system.domain.ro.UploadByUrlRo;
import org.springframework.web.multipart.MultipartFile;

import javax.servlet.http.HttpServletResponse;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.List;

/**
 * 参数配置 服务层
 *
 * @author ruoyi
 */
public interface ISysFileService
{
    /**
     * 查询文件管理
     *
     * @param ids 文件管理ID
     * @return 文件管理
     */
    public List<SysFile> selectSysFileByIds(String ids);

    public SysFile selectSysFileById(Long id);

    /**
     * 查询文件管理列表
     *
     * @param sysFile 文件管理
     * @return 文件管理集合
     */
    public List<SysFile> selectSysFileList(SysFile sysFile);
    /**
     * 新增或者修改文件管理
     *
     * @param sysFile 文件管理
     * @return 结果
     */
    public AjaxResult saveSysFile(SysFile sysFile);

    /**
     * 批量删除文件管理
     *
     * @param ids 需要删除的文件管理ID
     * @return 结果
     */
    public AjaxResult deleteSysFileByIds(Long[] ids);

    /**
     * 删除文件管理信息
     *
     * @param id 文件管理ID
     * @return 结果
     */
    public AjaxResult deleteSysFileById(Long id);


    /**
     * 上传文件
     * @param file
     * @return
     */
    AjaxResult uploadFile(MultipartFile file);

    AjaxResult uploadFiles(MultipartFile[] files);

    AjaxResult uploadByUrl(List<UploadByUrlRo> roList);

    AjaxResult uploadFilesUser(MultipartFile[] files,String userId);//直接传用户ID

    AjaxResult uploadSupplier(MultipartFile[] files,String[] bussNames);

    AjaxResult uploadFilesPdf(MultipartFile[] files,HttpServletResponse response);

    AjaxResult uploadFileId(Long fileId,MultipartFile files);

    AjaxResult uploadFilesEnc(MultipartFile[] files);

    /**
     * 读取文件
     * @param bucket 桶名称
     * @param fileName 文件名称
     * @param response 输出流
     */
    void getFile(String bucket, String fileName, HttpServletResponse response);

    /**
     * 读取文件
     * @param bucket 桶名称
     * @param fileName 文件名称
     * @param fileUrl 输出地址
     */
    void getFileToUrl(String bucket, String fileName, String fileUrl);

    /**
     * 更新CA驱动程序ID，写死3001
     * @param sysFile
     * @return
     */
    public AjaxResult updateCAFile(SysFile sysFile);

    /**
     * 获取文件外链
     * @param fileId 文件id
     * @return
     */
    String getFileUrl(Long fileId);

    /**
     * 上传base64后的图片
     * @param base64Picture
     * @param sysFile
     * @return
     */
    AjaxResult uploadBase64Picture(String base64Picture, SysFile sysFile);

    /**
     * 上传base64后的图片
     * @param richText
     * @return
     */
    String uploadBase64Picture(String richText);

    /**
     * 上传base64后的图片
     * @param bucket
     * @param fileName
     * @param os
     */
    void getFile(String bucket, String fileName, OutputStream os);

    /**
     * 上传文件
     * @param is
     * @param file
     * @return 文件id
     */
    Long uploadFile(InputStream is, SysFile file);

    /**
     * 获取文件流
     * @param sysFileId id
     * @return
     */
    S3Object getFileObject(Long sysFileId);

    /**
     * 获取byte数组
     * @param sysFileId id
     * @return
     */
    byte[] getByteObject(Long sysFileId);
}
