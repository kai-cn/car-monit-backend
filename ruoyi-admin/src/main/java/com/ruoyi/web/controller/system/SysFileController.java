package com.ruoyi.web.controller.system;

import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.system.domain.SysFile;
import com.ruoyi.system.service.ISysFileService;
import com.ruoyi.web.util.Base64DecodeMultipartFile;
import com.ruoyi.web.util.CommonUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import javax.servlet.http.HttpServletResponse;
import java.util.List;

/**
 * 参数配置 信息操作处理
 *
 * @author ruoyi
 */
@RestController
@RequestMapping("/system/file")
public class SysFileController extends BaseController {
    @Autowired
    private ISysFileService sysFileService;

    /**
     * 获取参数配置列表
     */
    @PreAuthorize("@ss.hasPermi('base:sysflie:list')")
    @GetMapping("/list")
    public TableDataInfo list(SysFile sysFile) {
        startPage();
        List<SysFile> list = sysFileService.selectSysFileList(sysFile);
        return getDataTable(list);
    }

    /**
     * 获取文件详细信息
     */
    @GetMapping(value = "/getInfoById/{id}")
    public AjaxResult getInfoById(@PathVariable("id") Long id) {
        return AjaxResult.success(sysFileService.selectSysFileById(id));
    }

    /**
     * 获取文件详细信息
     */
    @GetMapping(value = "/{ids}")
    public AjaxResult getInfo(@PathVariable("ids") String ids) {
        ids = CommonUtil.deleteEnd(ids);
        if (CommonUtil.isBlank(ids)) {
            ids = "-111111";
        }
        return AjaxResult.success(sysFileService.selectSysFileByIds(ids));
    }

    /**
     * 上传文件 文件名采用uuid,避免原始文件名中带"-"符号导致下载的时候解析出现异常
     *
     * @param files 资源
     * @return R(/ admin / bucketName / filename)
     */
    @PostMapping("/upload")
    @Log(title = "文件", businessType = BusinessType.INSERT)
    public AjaxResult upload(@RequestParam("files") MultipartFile[] files) {
        return sysFileService.uploadFiles(files);
    }

    /**
     * 上传文件 文件名采用uuid,避免原始文件名中带"-"符号导致下载的时候解析出现异常
     *
     * @param files 资源
     * @return R(/ admin / bucketName / filename)
     */
    @PostMapping("/uploadSupplier")
    @Log(title = "文件", businessType = BusinessType.INSERT)
    public AjaxResult uploadSupplier(@RequestParam("files") MultipartFile[] files,@RequestParam("bussNames") String[] bussNames) {
        return sysFileService.uploadSupplier(files,bussNames);
    }

    /**
     * 上传文件 文件名采用uuid,避免原始文件名中带"-"符号导致下载的时候解析出现异常
     *
     * @param files 资源
     * @return R(/ admin / bucketName / filename)
     */
    @PostMapping("/uploadPdf")
    @Log(title = "文件", businessType = BusinessType.INSERT)
    public AjaxResult uploadPdf(@RequestParam("files") MultipartFile[] files,HttpServletResponse response) {
        return sysFileService.uploadFilesPdf(files,response);
    }

    @GetMapping(value = "/{bucket}/{fileName}")
    public void file(@PathVariable String bucket, @PathVariable String fileName, HttpServletResponse response) {
        sysFileService.getFile(bucket, fileName, response);
    }

    @GetMapping(value = "/view/{bucket}/{fileName}")
    public void fileview(@PathVariable String bucket, @PathVariable String fileName, HttpServletResponse response) {
        sysFileService.getFile(bucket, fileName, response);
    }

    /**
     * 删除单个文件
     */
    @Log(title = "文件", businessType = BusinessType.DELETE)
    @DeleteMapping("/del/{id}")
    public AjaxResult removeById(@PathVariable Long id) {
        return sysFileService.deleteSysFileById(id);
    }

    /**
     * 删除多个文件
     */
    @PreAuthorize("@ss.hasPermi('base:supplier:remove')")
    @Log(title = "文件", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable Long[] ids) {
        return sysFileService.deleteSysFileByIds(ids);
    }


    /**
     * 上传文件 文件名采用uuid,避免原始文件名中带"-"符号导致下载的时候解析出现异常
     *
     * @param
     * @return R(/ admin / bucketName / filename)
     */
    @PostMapping("/uploadFileId")
    @Log(title = "文件", businessType = BusinessType.INSERT)
    public AjaxResult uploadFileId(@RequestBody SysFile sysFile) {

        if (CommonUtil.isNull(sysFile.getId()).equals("")) {
            AjaxResult.error("主键不能为空");
        }

        MultipartFile tempfiles = Base64DecodeMultipartFile.base64Convert(sysFile.getFiles());
        return sysFileService.uploadFileId(sysFile.getId(), tempfiles);
    }

    /**
     * 上传文件 文件名采用uuid,避免原始文件名中带"-"符号导致下载的时候解析出现异常
     *
     * @param files 资源
     * @return R(/ admin / bucketName / filename)
     */
    @PostMapping("/uploadFileEnc")
    @Log(title = "文件", businessType = BusinessType.INSERT)
    public AjaxResult uploadFileEnc(@RequestParam("files") MultipartFile[] files) {
        return sysFileService.uploadFilesEnc(files);
    }

    /**
     * 修改文件管理
     */
    @Log(title = "文件管理", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody SysFile sysFile)
    {
        return sysFileService.saveSysFile(sysFile);
    }

    /**
     * 获取最新的CA驱动程序
     */
    @GetMapping("/getNewCa")
    public AjaxResult getNewCa(SysFile sysFile) {
        startPage();
        List<SysFile> list = sysFileService.selectSysFileList(sysFile);

        if (list.size()>0){
            return AjaxResult.success(list.get(0));
        }

        return AjaxResult.error("未找到CA驱动程序");
    }

    @Log(title = "文件", businessType = BusinessType.UPDATE)
    @PostMapping("/updateCAFile")
    public AjaxResult updateCAFile(@RequestBody SysFile sysFile) {
        return sysFileService.updateCAFile(sysFile);
    }
}
