package com.ruoyi.system.service.impl;

import cn.hutool.core.io.FileUtil;
import cn.hutool.core.io.IoUtil;
import cn.hutool.core.util.IdUtil;
import cn.hutool.core.util.StrUtil;
import com.amazonaws.services.s3.model.S3Object;
import com.amazonaws.services.s3.model.S3ObjectInputStream;
import com.ruoyi.common.config.OssProperties;
import com.ruoyi.common.config.RuoYiConfig;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.*;
import com.ruoyi.common.utils.http.OssTemplate;
import com.ruoyi.common.utils.sign.Base64;
import com.ruoyi.system.domain.SysFile;
import com.ruoyi.system.domain.ro.UploadByUrlRo;
import com.ruoyi.system.mapper.SysFileMapper;
import com.ruoyi.system.service.ISysFileService;
import com.ruoyi.system.service.forest.FileApi;
import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.io.IOUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import jakarta.annotation.Resource;
import jakarta.servlet.http.HttpServletResponse;
import java.io.*;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 参数配置 服务层实现
 *
 * @author ruoyi
 */
@Slf4j
@Service
@AllArgsConstructor
public class SysFileServiceImpl implements ISysFileService {
    private final OssProperties ossProperties;
    private final OssTemplate ossTemplate;
    @Autowired
    private SysFileMapper sysFileMapper;


    @Autowired
    private SnowflakeIdWorker idWorker;

    @Resource
    private FileApi fileApi;


    /**
     * 查询文件管理
     *
     * @param ids 文件管理ID
     * @return 文件管理
     */
    @Override
    public List<SysFile> selectSysFileByIds(String ids) {
        return sysFileMapper.selectSysFileByIds(ids.split("," ));
    }

    @Override
    public SysFile selectSysFileById(Long id) {
        return sysFileMapper.selectSysFileById(id);
    }

    /**
     * 查询文件管理列表
     *
     * @param sysFile 文件管理
     * @return 文件管理
     */
    @Override
    public List<SysFile> selectSysFileList(SysFile sysFile) {
        return sysFileMapper.selectSysFileList(sysFile);
    }

    /**
     * 新增或者修改文件管理
     *
     * @param sysFile 文件管理
     * @return 结果
     */
    @Override
    public AjaxResult saveSysFile(SysFile sysFile) {
        Long userId = SecurityUtils.getUserId();
        java.sql.Timestamp curDate = DateUtils.getTimestamp();
        if (sysFile.getId() != null) {
            // 修改
            sysFile.setUpdateUser(userId.toString()); // 更新人
            sysFile.setUpdateTime(curDate); // 更新时间
            sysFileMapper.updateSysFile(sysFile);
        } else {
            // 新增
            sysFile.setDelFlag("0" );
            sysFile.setCreateUser(userId.toString()); // 创建人
            sysFile.setCreateTime(curDate); // 创建时间
            sysFile.setUpdateUser(userId.toString()); // 更新人
            sysFile.setUpdateTime(curDate); // 更新时间

            // 主键手动赋值
            sysFile.setId(idWorker.nextId());

            sysFileMapper.insertSysFile(sysFile);
        }
        return AjaxResult.success("操作成功！" , sysFile.getId());
    }


    /**
     * 批量删除文件管理
     *
     * @param ids 需要删除的文件管理ID
     * @return 结果
     */
    @Override
    public AjaxResult deleteSysFileByIds(Long[] ids) {
        try {
            for (Long id : ids) {
                SysFile file = sysFileMapper.selectSysFileById(id);
                ossTemplate.removeObject(ossProperties.getBucketName(), file.getFileName());
            }
            int count = sysFileMapper.deleteSysFileByIds(ids);
            return AjaxResult.success(count);
        } catch (Exception ex) {
            return AjaxResult.error(ex.getMessage());
        }
    }

    /**
     * 删除文件管理信息
     *
     * @param id 文件管理ID
     * @return 结果
     */
    @Override
    public AjaxResult deleteSysFileById(Long id) {
        try {
            SysFile file = sysFileMapper.selectSysFileById(id);
            ossTemplate.removeObject(ossProperties.getBucketName(), file.getFileName());
            int count = sysFileMapper.deleteSysFileById(id);
            return AjaxResult.success(count);
        } catch (Exception ex) {
            return AjaxResult.error(ex.getMessage());
        }
    }

    /**
     * 上传文件
     *
     * @param file
     * @return
     */
    @Override
    public AjaxResult uploadFile(MultipartFile file) {
        String fileName = IdUtil.simpleUUID() + StrUtil.DOT + FileUtil.extName(file.getOriginalFilename());
        Map<String, String> resultMap = new HashMap<>(4);
        resultMap.put("bucketName" , ossProperties.getBucketName());
        resultMap.put("fileName" , fileName);
        resultMap.put("url" , String.format("/system/file/%s/%s" , ossProperties.getBucketName(), fileName));

        try {
            ossTemplate.putObject(ossProperties.getBucketName(), fileName, file.getInputStream());
            // 文件管理数据记录,收集管理追踪文件
            long fileId = fileLog(file, fileName);
            resultMap.put("id" , String.valueOf(fileId));
        } catch (Exception e) {
//            log.error("上传失败", e);
            return AjaxResult.error(e.getLocalizedMessage());
        }
        return AjaxResult.success(resultMap);
    }

    /**
     * 上传文件
     *
     * @param files
     * @return
     */
    @Override
    public AjaxResult uploadFiles(MultipartFile[] files) {
        List<Map> resultMaps = new ArrayList<>();
        for (MultipartFile file : files) {
            String fileName = IdUtil.simpleUUID() + StrUtil.DOT + FileUtil.extName(file.getOriginalFilename());
            Map<String, String> resultMap = new HashMap<>(4);
            resultMap.put("bucketName" , ossProperties.getBucketName());
            resultMap.put("fileName" , fileName);
            resultMap.put("url" , String.format("/system/file/%s/%s" , ossProperties.getBucketName(), fileName));

            try {
                // 文件管理数据记录,收集管理追踪文件
                Long fileId = fileLog(file, fileName);
                resultMap.put("id" , String.valueOf(fileId));
                if (!fileId.equals(-1L)) {
                    ossTemplate.putObject(ossProperties.getBucketName(), fileName, file.getInputStream());
                }
            } catch (Exception e) {
//                log.error("上传失败", e);
                return AjaxResult.error(e.getLocalizedMessage());
            }
            resultMaps.add(resultMap);
        }
        return AjaxResult.success(resultMaps);
    }

    /**
     * 上传文件
     *
     * @param roList 文件名, url
     * @return
     */
    @Override
    public AjaxResult uploadByUrl(List<UploadByUrlRo> roList) {
        List<Map> resultMaps = new ArrayList<>();
        for (UploadByUrlRo ro : roList) {
            ro.setFileName(CommonUtil.isNull(ro.getFileName())+".jpg");
            if (CommonUtil.isNotBlank(ro.getUrl())){
                try {
                    byte[] bytes = fileApi.downloadImageToByteArray(ro.getUrl());
                    MultipartFile file = MultipartFileUtil.convertByteToMultipartFile(bytes, ro.getFileName());
                    String fileName = IdUtil.simpleUUID() + StrUtil.DOT + FileUtil.extName(file.getOriginalFilename());
                    Map<String, String> resultMap = new HashMap<>(4);
                    resultMap.put("bucketName" , ossProperties.getBucketName());
                    resultMap.put("fileName" , fileName);
                    resultMap.put("url" , String.format("/system/file/%s/%s" , ossProperties.getBucketName(), fileName));

                    // 文件管理数据记录,收集管理追踪文件
                    Long fileId = fileLog(file, fileName);
                    resultMap.put("id" , String.valueOf(fileId));
                    if (!fileId.equals(-1L)) {
                        ossTemplate.putObject(ossProperties.getBucketName(), fileName, file.getInputStream());
                    }
                    resultMaps.add(resultMap);
                } catch (Exception e) {
                    log.error("上传失败", e);
                  //   return AjaxResult.error(e.getLocalizedMessage());
                }

            }
        }
        return AjaxResult.success(resultMaps);
    }

    @Override
    public AjaxResult uploadFilesUser(MultipartFile[] files,String userId) {
        List<Map> resultMaps = new ArrayList<>();
        for (MultipartFile file : files) {
            String fileName = IdUtil.simpleUUID() + StrUtil.DOT + FileUtil.extName(file.getOriginalFilename());
            Map<String, String> resultMap = new HashMap<>(4);
            resultMap.put("bucketName" , ossProperties.getBucketName());
            resultMap.put("fileName" , fileName);
            resultMap.put("url" , String.format("/system/file/%s/%s" , ossProperties.getBucketName(), fileName));

            try {
                // 文件管理数据记录,收集管理追踪文件
                Long fileId = fileLogUser(file, fileName,userId);
                resultMap.put("id" , String.valueOf(fileId));
                if (!fileId.equals(-1L)) {
                    ossTemplate.putObject(ossProperties.getBucketName(), fileName, file.getInputStream());
                }
            } catch (Exception e) {
//                log.error("上传失败", e);
                return AjaxResult.error(e.getLocalizedMessage());
            }
            resultMaps.add(resultMap);
        }
        return AjaxResult.success(resultMaps);
    }

    /**
     * 上传文件
     *
     * @param files
     * @param bussNames
     * @return
     */
    @Override
    public AjaxResult uploadSupplier(MultipartFile[] files,String[] bussNames) {
        List<Map> resultMaps = new ArrayList<>();
        for (int i = 0; i < files.length; i++) {
            MultipartFile file = files[i];
            String bussName = bussNames[i];
            String fileName = IdUtil.simpleUUID() + StrUtil.DOT + FileUtil.extName(file.getOriginalFilename());
            Map<String, String> resultMap = new HashMap<>(4);
            resultMap.put("bucketName" , ossProperties.getBucketName());
            resultMap.put("fileName" , fileName);
            resultMap.put("url" , String.format("/system/file/%s/%s" , ossProperties.getBucketName(), fileName));

            try {
                // 文件管理数据记录,收集管理追踪文件
                Long fileId = fileSupplierLog(file, fileName,bussName);
                resultMap.put("id" , String.valueOf(fileId));
                if (!fileId.equals(-1L)) {
                    ossTemplate.putObject(ossProperties.getBucketName(), fileName, file.getInputStream());
                }
            } catch (Exception e) {
                return AjaxResult.error(e.getLocalizedMessage());
            }
            resultMaps.add(resultMap);
        }
        return AjaxResult.success(resultMaps);
    }


    /**
     * 上传文件 --转成pdf格式
     *
     * @param files
     * @return
     */
    @Override
    public AjaxResult uploadFilesPdf(MultipartFile[] files, HttpServletResponse response) {
        List<Map> resultMaps = new ArrayList<>();
        for (MultipartFile file : files) {
            String fileName = IdUtil.simpleUUID() + StrUtil.DOT + FileUtil.extName(file.getOriginalFilename());
            Map<String, String> resultMap = new HashMap<>(4);
            resultMap.put("bucketName" , ossProperties.getBucketName());
            resultMap.put("fileName" , fileName);
            resultMap.put("url" , String.format("/system/file/%s/%s" , ossProperties.getBucketName(), fileName));

            String original = file.getOriginalFilename();
            String ext = FileUtil.extName(original);
            if (ext.equals("pdf" )) {
                // 如果是pdf
                try {
                    // 文件管理数据记录,收集管理追踪文件
                    Long fileId = fileLog(file, fileName);
                    resultMap.put("id" , String.valueOf(fileId));
                    if (!fileId.equals(-1L)) {
                        ossTemplate.putObject(ossProperties.getBucketName(), fileName, file.getInputStream());
                    }
                } catch (Exception e) {
//                log.error("上传失败", e);
                    return AjaxResult.error(e.getLocalizedMessage());
                }
            } else {
                // 文件转换
                OutputStream out = null;
                FileInputStream fileInputStream = null;
                InputStream inputStream = null;
                String simpleUUID = IdUtil.simpleUUID();
                try {
                    String uuid = StringUtils.getUUID();
                    String urls = RuoYiConfig.getUploadPath() + "/" + uuid;
                    out = response.getOutputStream();
                    File file1 = new File(urls);
                    if (!file1.exists()) {
                        file1.mkdirs();
                    }

                    //文件上传本地路径
                    String filePath = urls + "/" + fileName;

                    //文件上传pdf本地路径
                    String pdfName = file.getOriginalFilename().replaceAll(".docx" , ".pdf" ).replaceAll(".doc" , ".pdf" );
                    String pdfFilePath = urls + "/" + fileName.replaceAll(".docx" , ".pdf" ).replaceAll(".doc" , ".pdf" );

                    //输出文件
                    out = new FileOutputStream(new File(filePath));

                    inputStream = file.getInputStream();

                    // 进行写操作
                    int len = 0;
                    byte[] bytes = new byte[1024];
                    while ((len = inputStream.read(bytes)) > 0) {
                        out.write(bytes, 0, len);
                    }
                    inputStream.close();
                    out.flush();
                    out.close();

                    //转pdf
                   /* WordToPdf wordToPdf = new WordToPdf();
                    wordToPdf.change(filePath, pdfFilePath);

                    //File转MultipartFile
                    File pdfFile = new File(pdfFilePath);
                    fileInputStream = new FileInputStream(pdfFile);
                    MultipartFile multipartFile = new MockMultipartFile(pdfName, pdfName,
                            ContentType.APPLICATION_OCTET_STREAM.toString(), fileInputStream);

                    fileName = simpleUUID + StrUtil.DOT + FileUtil.extName(multipartFile.getOriginalFilename());

                    resultMap.put("fileName" , fileName);
                    resultMap.put("url" , String.format("/system/file/%s/%s" , ossProperties.getBucketName(), fileName));

                    // 文件管理数据记录,收集管理追踪文件
                    Long fileId = fileLog(multipartFile, fileName);
                    resultMap.put("id" , String.valueOf(fileId));
                    fileInputStream.close();

                    if (!fileId.equals(-1L)) {
                        ossTemplate.putObject(ossProperties.getBucketName(), fileName, multipartFile.getInputStream());
                        File workFile = new File(filePath);
                        if (workFile.exists()) {
                            workFile.delete();
                        }
                        if (pdfFile.exists()) {
                            pdfFile.delete();
                        }
                    }*/
                } catch (Exception e) {
//                log.error("上传失败", e);
                    return AjaxResult.error(e.getLocalizedMessage());
                }
            }
            resultMaps.add(resultMap);
        }
        return AjaxResult.success(resultMaps);
    }

    /**
     * 读取文件
     *
     * @param bucket
     * @param fileName
     * @param response
     */
    @Override
    public void getFile(String bucket, String fileName, HttpServletResponse response) {
        try (S3Object s3Object = ossTemplate.getObject(bucket, fileName)) {
            response.setContentType("application/octet-stream; charset=UTF-8" );
            IoUtil.copy(s3Object.getObjectContent(), response.getOutputStream());
        } catch (Exception e) {
//            log.error("文件读取异常: {}", e.getLocalizedMessage());
        }
    }

    @Override
    public void getFileToUrl(String bucket, String fileName, String fileUrl) {
        try (S3Object s3Object = ossTemplate.getObject(bucket, fileName)) {
            S3ObjectInputStream objectContent = s3Object.getObjectContent();
            FileOutputStream fos = new FileOutputStream(new File(fileUrl+ "/" +fileName ));
            byte[] read_buf = new byte[1024];
            int read_len = 0;
            while((read_len = objectContent.read(read_buf))>0){
                fos.write(read_buf,0,read_len);
            }
            objectContent.close();
            fos.close();
        } catch (Exception e) {
           log.error("文件读取异常: {}", e.getLocalizedMessage());
        }
    }

    public static String convert(String source, Charset srcCharset, Charset destCharset) {
        if (null == srcCharset) {
            srcCharset = StandardCharsets.ISO_8859_1;
        }

        if (null == destCharset) {
            destCharset = StandardCharsets.UTF_8;
        }

        return !StrUtil.isBlank(source) && !srcCharset.equals(destCharset) ? new String(source.getBytes(srcCharset), destCharset) : source;
    }

    /**
     * 文件管理数据记录,收集管理追踪文件
     *
     * @param file     上传文件格式
     * @param fileName 文件名
     */
    private Long fileLog(MultipartFile file, String fileName) {
        SysFile sysFile = new SysFile();
        // 原文件名
        // String original = convert(file.getOriginalFilename(), CharsetUtil.ISO_8859_1, CharsetUtil.UTF_8);
        String original = file.getOriginalFilename();
        sysFile.setFileName(fileName);
        sysFile.setOriginal(original);
        sysFile.setFileSize(file.getSize());
        String ext = FileUtil.extName(original);
        if (null != ext && !ext.equals("" )) {
            ext = ext.toLowerCase();
            if (ext.indexOf("doc" ) > -1 || ext.indexOf("docx" ) > -1 || ext.indexOf("pdf" ) > -1 || ext.indexOf("xls" ) > -1
                    || ext.indexOf("xlsx" ) > -1 || ext.indexOf("pptx" ) > -1 || ext.indexOf("txt" ) > -1 || ext.indexOf("zip" ) > -1 || ext.indexOf("rar" ) > -1
                    || ext.indexOf("jpg" ) > -1 || ext.indexOf("jpeg" ) > -1 || ext.indexOf("png" ) > -1 || ext.indexOf("gif" ) > -1
                    || ext.indexOf("mp3" ) > -1 || ext.indexOf("mp4" ) > -1 || ext.indexOf("flv" ) > -1 || ext.indexOf("3gp" ) > -1
                    ) {
                sysFile.setType(ext);
                sysFile.setBucketName(ossProperties.getBucketName());
                sysFile.setCreateUser(SecurityUtils.getUserId().toString());
                sysFile.setCreateUser(SecurityUtils.getUserId().toString());
                this.saveSysFile(sysFile);
            } else {
                sysFile.setId(-1L);
            }
        } else {
            sysFile.setId(-1L);
        }
        return sysFile.getId();
    }

    /**
     * 文件管理数据记录,收集管理追踪文件
     *
     * @param file     上传文件格式
     * @param fileName 文件名
     * @param bussName 有效期
     */
    private Long fileSupplierLog(MultipartFile file, String fileName,String bussName) {
        SysFile sysFile = new SysFile();
        // 原文件名
        // String original = convert(file.getOriginalFilename(), CharsetUtil.ISO_8859_1, CharsetUtil.UTF_8);
        String original = file.getOriginalFilename();
        sysFile.setFileName(fileName);
        sysFile.setBussName(bussName);
        sysFile.setOriginal(original);
        sysFile.setFileSize(file.getSize());
        String ext = FileUtil.extName(original);
        if (null != ext && !ext.equals("" )) {
            ext = ext.toLowerCase();
            if (ext.indexOf("doc" ) > -1 || ext.indexOf("docx" ) > -1 || ext.indexOf("pdf" ) > -1 || ext.indexOf("xls" ) > -1
                    || ext.indexOf("xlsx" ) > -1 || ext.indexOf("pptx" ) > -1 || ext.indexOf("txt" ) > -1 || ext.indexOf("zip" ) > -1 || ext.indexOf("rar" ) > -1
                    || ext.indexOf("jpg" ) > -1 || ext.indexOf("jpeg" ) > -1 || ext.indexOf("png" ) > -1 || ext.indexOf("gif" ) > -1
                    || ext.indexOf("mp3" ) > -1 || ext.indexOf("mp4" ) > -1 || ext.indexOf("flv" ) > -1 || ext.indexOf("3gp" ) > -1
                    ) {
                sysFile.setType(ext);
                sysFile.setBucketName(ossProperties.getBucketName());
                sysFile.setCreateUser(SecurityUtils.getUserId().toString());
                sysFile.setCreateUser(SecurityUtils.getUserId().toString());
                this.saveSysFile(sysFile);
            } else {
                sysFile.setId(-1L);
            }
        } else {
            sysFile.setId(-1L);
        }
        return sysFile.getId();
    }


    /**
     * 上传文件
     *
     * @param file
     * @return
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult uploadFileId(Long fileId, MultipartFile file) {
        List<Map> resultMaps = new ArrayList<>();

        String fileName = IdUtil.simpleUUID() + StrUtil.DOT + FileUtil.extName(file.getOriginalFilename());
        Map<String, String> resultMap = new HashMap<>(4);
        resultMap.put("bucketName" , ossProperties.getBucketName());
        resultMap.put("fileName" , fileName);
        resultMap.put("url" , String.format("/system/file/%s/%s" , ossProperties.getBucketName(), fileName));

        try {

            // 文件管理数据记录,收集管理追踪文件
            fileLogId(file, fileName, fileId);
            resultMap.put("id" , String.valueOf(fileId));
            if (!fileId.equals(-1L)) {
                ossTemplate.putObject(ossProperties.getBucketName(), fileName, file.getInputStream());
            }
        } catch (Exception e) {
//                log.error("上传失败", e);
            return AjaxResult.error(e.getLocalizedMessage());
        }
        resultMaps.add(resultMap);

        return AjaxResult.success(resultMaps);
    }

    /**
     * 文件管理数据记录,收集管理追踪文件
     *
     * @param file     上传文件格式
     * @param fileName 文件名
     */
    private Long fileLogId(MultipartFile file, String fileName, Long fileId) {
        SysFile sysFile = new SysFile();
        // 原文件名
        // String original = convert(file.getOriginalFilename(), CharsetUtil.ISO_8859_1, CharsetUtil.UTF_8);
        String original = file.getOriginalFilename();
        sysFile.setFileName(fileName);
        sysFile.setOriginal(original);
        sysFile.setFileSize(file.getSize());
        String ext = FileUtil.extName(original);
        if (null != ext && !ext.equals("" )) {
            ext = ext.toLowerCase();
            if (ext.indexOf("doc" ) > -1 || ext.indexOf("docx" ) > -1 || ext.indexOf("pdf" ) > -1 || ext.indexOf("xls" ) > -1 || ext.indexOf("txt" ) > -1
                    || ext.indexOf("xlsx" ) > -1 || ext.indexOf(".ppt" ) > -1 || ext.indexOf("pptx" ) > -1 || ext.indexOf("zip" ) > -1 || ext.indexOf("rar" ) > -1
                    || ext.indexOf("jpg" ) > -1 || ext.indexOf("jpeg" ) > -1 || ext.indexOf("png" ) > -1 || ext.indexOf("gif" ) > -1
                    || ext.indexOf("mp3" ) > -1 || ext.indexOf("mp4" ) > -1 || ext.indexOf("flv" ) > -1 || ext.indexOf("3gp" ) > -1
                    ) {

                // 先删除 后新增
                this.deleteSysFileByIdNew(fileId);

                sysFile.setId(fileId);
                sysFile.setType(ext);
                sysFile.setBucketName(ossProperties.getBucketName());

                Long userId = SecurityUtils.getUserId();
                java.sql.Timestamp curDate = DateUtils.getTimestamp();
                // 新增
                sysFile.setDelFlag("0" );
                sysFile.setCreateUser(userId.toString()); // 创建人
                sysFile.setCreateTime(curDate); // 创建时间
                sysFile.setUpdateUser(userId.toString()); // 更新人
                sysFile.setUpdateTime(curDate); // 更新时间
                sysFileMapper.insertSysFile(sysFile);

            } else {
                sysFile.setId(-1L);
            }
        } else {
            sysFile.setId(-1L);
        }
        return sysFile.getId();
    }


    /**
     * 删除文件管理信息
     *
     * @param id 文件管理ID
     * @return 结果
     */
    public void deleteSysFileByIdNew(Long id) {
        try {
            SysFile file = sysFileMapper.selectSysFileById(id);
            ossTemplate.removeObject(ossProperties.getBucketName(), file.getFileName());
            int count = sysFileMapper.deleteSysFileByIdNew(id);
        } catch (Exception ex) {
        }
    }


    /**
     * 上传文件并加密
     *
     * @param files
     * @return
     */
    @Override
    public AjaxResult uploadFilesEnc(MultipartFile[] files) {
        List<Map> resultMaps = new ArrayList<>();
        for (MultipartFile file : files) {
           /* //  String fileName = IdUtil.simpleUUID() + StrUtil.DOT + FileUtil.extName(file.getOriginalFilename()) + StrUtil.DOT + "enc";
            String fileName = IdUtil.simpleUUID() + StrUtil.DOT + FileUtil.extName(file.getOriginalFilename());
            Map<String, String> resultMap = new HashMap<>(4);
            resultMap.put("bucketName", ossProperties.getBucketName());
            resultMap.put("fileName", fileName);
            resultMap.put("url", String.format("/system/file/%s/%s", ossProperties.getBucketName(), fileName));

            InputStream filObj = null;
            try {
                filObj = caService.encodeEnvelopedFile(file.getInputStream());
            } catch (IOException e) {
                log.error("uploadFilesEnc  encode error, fileName:" + fileName + " ,errMsg:" + e.getMessage());
                e.printStackTrace();
            }
            try {
                // 文件管理数据记录,收集管理追踪文件
                Long fileId = fileLog(file, fileName);
                resultMap.put("id", String.valueOf(fileId));
                if (!fileId.equals(-1L)) {
                    ossTemplate.putObject(ossProperties.getBucketName(), fileName, filObj);
                }
            } catch (Exception e) {
//                log.error("上传失败", e);
                return AjaxResult.error(e.getLocalizedMessage());
            }
            resultMaps.add(resultMap); */
        }
        return AjaxResult.success(resultMaps);
    }

    /**
     * 更新CA驱动程序ID，写死3001
     * @param sysFile
     * @return
     */
    @Override
    public AjaxResult updateCAFile(SysFile sysFile) {
        Long userId = SecurityUtils.getUserId();
        java.sql.Timestamp curDate = DateUtils.getTimestamp();
        sysFile.setUpdateUser(userId.toString()); // 更新人
        sysFile.setUpdateTime(curDate); // 更新时间

        // 新删除ID为3001的文件
        this.deleteSysFileByIdNew(3001L);

        sysFileMapper.updateCAFile(sysFile);

        return AjaxResult.success("操作成功！" , sysFile.getId());
    }

    /**
     * 获取文件外链
     * @param fileId 文件id
     * @return
     */
    @Override
    public String getFileUrl(Long fileId) {
      /*  if (fileId == null) {
            return null;
        }

        SysFile sysFile = this.selectSysFileById(fileId);
        if (sysFile == null ||
                StringUtils.isAnyBlank(sysFile.getBucketName(), sysFile.getFileName())) {

            return null;
        }

        return Constants.FILE_LINK_PREFIX + Constants.CHAR_SLASH + sysFile.getBucketName() + Constants.CHAR_SLASH + sysFile.getFileName();*/

        return null;
    }

    /**
     * 上传base64后的图片
     * @param base64Picture
     * @param sysFile
     * @return
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult uploadBase64Picture(String base64Picture, SysFile sysFile) {
        byte[] decode = Base64.decode(base64Picture);
        ByteArrayInputStream byteArrayInputStream = null;
        String fileName = IdUtil.simpleUUID() + StrUtil.DOT + sysFile.getType();

        try {
            byteArrayInputStream = new ByteArrayInputStream(decode);

            // 保存上传图片的信息
            sysFile.setFileName(fileName);
            AjaxResult ajaxResult = this.saveSysFile(sysFile);
            if (!"200".equals(String.valueOf(ajaxResult.get(AjaxResult.CODE_TAG))))  {
                return AjaxResult.error("上传图片失败!");
            }
            String fileId = String.valueOf(ajaxResult.get(AjaxResult.DATA_TAG));

            // 上传文件
            Map<String, String> resultMap = new HashMap<>(4);
            resultMap.put("bucketName" , ossProperties.getBucketName());
            resultMap.put("fileName" , fileName);
            resultMap.put("url" , String.format("/system/file/%s/%s" , ossProperties.getBucketName(), fileName));
            resultMap.put("id" , fileId);

            OssTemplate.putObject(ossProperties.getBucketName(), fileName, byteArrayInputStream);

            return AjaxResult.success(fileId);
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            IOUtils.closeQuietly(byteArrayInputStream);
        }

        return AjaxResult.error();
    }

    /**
     * 上传base64后的图片
     * @param richText
     * @return
     */
    @Override
    public String uploadBase64Picture(String richText) {
        if (StringUtils.isBlank(richText)) {
            return richText;
        }

        /*List<String> imageSrcValueList = StringUtils.getImgSrc(richText);
        List<String> fileIdList = new ArrayList<>(imageSrcValueList.size());
        if (CollectionUtils.isNotEmpty(imageSrcValueList)) {
            imageSrcValueList.forEach(srcValue -> {
                // 分割base64图片和说明部分
                String[] separationArray = srcValue.split(Constants.BASE64_FLAG);
                // base64图片说明部分
                String instructions = separationArray[0];
                // base64编码的图片部分
                String base64Picture = separationArray[1];
                // 图片后缀名
                String suffix = instructions.replaceAll(Constants.CHAR_SEMICOLON, Constants.CHAR_BLANK)
                                     .split(Constants.CHAR_SLASH)[1];

                // 构造文件上传对象信息
                SysFile sysFile = new SysFile();
                sysFile.setType(suffix);
                sysFile.setBucketName(ossProperties.getBucketName());

                // 上传文件
                AjaxResult ajaxResult = this.uploadBase64Picture(base64Picture, sysFile);
                if ("200".equals(String.valueOf(ajaxResult.get(AjaxResult.CODE_TAG)))) {
                    if (ajaxResult.get(AjaxResult.MSG_TAG) != null) {
                        fileIdList.add(String.valueOf(ajaxResult.get(AjaxResult.MSG_TAG)));
                    }
                }
            });
        }

        // 替换内容
        if (CollectionUtils.isNotEmpty(fileIdList)) {
            return RichTextPictureUtil.setImagesSrcValue(richText, fileIdList);
        }

        return Constants.CHAR_BLANK;*/

        return "";
    }

    private Long fileLogUser(MultipartFile file, String fileName,String userId) {
        SysFile sysFile = new SysFile();
        java.sql.Timestamp curDate = DateUtils.getTimestamp();
        // 原文件名
        // String original = convert(file.getOriginalFilename(), CharsetUtil.ISO_8859_1, CharsetUtil.UTF_8);
        String original = file.getOriginalFilename();
        sysFile.setFileName(fileName);
        sysFile.setOriginal(original);
        sysFile.setFileSize(file.getSize());
        String ext = FileUtil.extName(original);
        if (null != ext && !ext.equals("" )) {
            ext = ext.toLowerCase();
            if (ext.indexOf("doc" ) > -1 || ext.indexOf("docx" ) > -1 || ext.indexOf("pdf" ) > -1 || ext.indexOf("xls" ) > -1
                    || ext.indexOf("xlsx" ) > -1 || ext.indexOf("pptx" ) > -1 || ext.indexOf("txt" ) > -1 || ext.indexOf("zip" ) > -1 || ext.indexOf("rar" ) > -1
                    || ext.indexOf("jpg" ) > -1 || ext.indexOf("jpeg" ) > -1 || ext.indexOf("png" ) > -1 || ext.indexOf("gif" ) > -1
                    || ext.indexOf("mp3" ) > -1 || ext.indexOf("mp4" ) > -1 || ext.indexOf("flv" ) > -1 || ext.indexOf("3gp" ) > -1
            ) {
                sysFile.setType(ext);
                sysFile.setBucketName(ossProperties.getBucketName());
                sysFile.setCreateUser(userId);
                sysFile.setCreateUser(userId);
                sysFile.setCreateTime(curDate);
                sysFile.setUpdateTime(curDate);

                sysFile.setId(idWorker.nextId());

                sysFileMapper.insertSysFile(sysFile);
            } else {
                sysFile.setId(-1L);
            }
        } else {
            sysFile.setId(-1L);
        }
        return sysFile.getId();
    }

    /**
     * 读取文件
     *
     * @param bucket
     * @param fileName
     * @param os
     */
    @Override
    public void getFile(String bucket, String fileName, OutputStream os) {
        try (S3Object s3Object = ossTemplate.getObject(bucket, fileName)) {
            IoUtil.copy(s3Object.getObjectContent(), os);
        } catch (Exception e) {
//            log.error("文件读取异常: {}", e.getLocalizedMessage());
        }
    }

    @Transactional(rollbackFor = Exception.class)
    @Override
    public Long uploadFile(InputStream is, SysFile sysFile) {
        try {
            /*String bucketName = sysFile.getBucketName();
            String fileName = sysFile.getFileName();
            File file = new File(bucketName+fileName);
            FileItem fileItem = new DiskFileItem("file", Files.probeContentType(file.toPath()), false, file.getName(), (int) file.length(), file.getParentFile());
            fileItem.getOutputStream();
            MultipartFile multipartFile = new CommonsMultipartFile(fileItem);
            //生成新文件名
            fileName = IdUtil.simpleUUID() + StrUtil.DOT + FileUtil.extName(multipartFile.getOriginalFilename());
            //上传文件流
            ossTemplate.putObject(bucketName, fileName, is);

            //新增sys_file表数据
            SysFile sysFileNew = new SysFile();
            BeanUtil.copyProperties(sysFile,sysFileNew);
            // sysFileNew.setId(null);
            sysFileNew.setId(idWorker.nextId());
            sysFileNew.setFileName(fileName);
            sysFileNew.setOriginal(multipartFile.getOriginalFilename());
            sysFileNew.setFileSize(multipartFile.getSize());

            sysFileMapper.insertSysFile(sysFileNew);
            log.info("sys_file表数据新增成功,文件id:{}",sysFileNew.getId());
            return sysFileNew.getId();*/
            return  idWorker.nextId();
        } catch (Exception e) {
            log.error("上传失败：{}",e.getMessage());
        }
        return null;
    }

    @Override
    public S3Object getFileObject(Long sysFileId) {
        SysFile sysFile = this.selectSysFileById(sysFileId);
        if(sysFile != null){
            try {
                return ossTemplate.getObjectInfo(sysFile.getBucketName(), sysFile.getFileName());
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
        return null;
    }

    @Override
    public byte[] getByteObject(Long sysFileId) {
        SysFile sysFile = this.selectSysFileById(sysFileId);
        if(sysFile != null){
            try {
                S3Object s3Object = ossTemplate.getObjectInfo(sysFile.getBucketName(), sysFile.getFileName());
                InputStream inputStream = s3Object.getObjectContent();

                // 创建一个ByteArrayOutputStream
                ByteArrayOutputStream outputStream = new ByteArrayOutputStream();

                // 创建一个缓冲区
                byte[] buffer = new byte[1024];
                int length;

                // 从InputStream读取数据，并写入到ByteArrayOutputStream
                while ((length = inputStream.read(buffer)) != -1) {
                    outputStream.write(buffer, 0, length);
                }

                // 将ByteArrayOutputStream转换为字节数组
                byte[] finalBytes = outputStream.toByteArray();


                inputStream.close();
                outputStream.close();
                return finalBytes;
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
        return null;
    }


}
