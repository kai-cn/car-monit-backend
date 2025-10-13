package com.ruoyi.common.utils;


import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.util.Objects;

import com.ruoyi.common.exception.CustomException;
import org.apache.commons.fileupload.FileItem;
import org.apache.commons.fileupload.FileItemFactory;
import org.apache.commons.fileupload.disk.DiskFileItem;
import org.apache.commons.fileupload.disk.DiskFileItemFactory;
import org.apache.commons.io.IOUtils;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.multipart.commons.CommonsMultipartFile;

import java.io.*;

public class MultipartFileUtil {

    public static MultipartFile convertByteToMultipartFile(byte[] imageBytes, String fileName) {
        if (Objects.isNull(imageBytes)) {
            throw new CustomException("输入 byte 数组为空，转换失败");
        }
        String contentType = "image/jpeg";
        FileItem item;
        try {
            FileItemFactory factory = new DiskFileItemFactory();
            item = factory.createItem("file", contentType, false, fileName);
            try (ByteArrayOutputStream bos = new ByteArrayOutputStream(imageBytes.length);
                 OutputStream os = item.getOutputStream()) {
                bos.write(imageBytes);
                os.write(bos.toByteArray());
            }
            return new CommonsMultipartFile(item);
        } catch (IOException e) {
            throw new CustomException("转换过程中发生错误", e);
        }
    }


    public static MultipartFile convertInputStreamToMultipartFile(InputStream inputStream, String fileName) {
        DiskFileItem fileItem = (DiskFileItem) new DiskFileItemFactory().createItem("file", "text/plain", true, fileName);
        try (OutputStream os = fileItem.getOutputStream()) {
            IOUtils.copy(inputStream, os);
        } catch (IOException e) {
            throw new IllegalArgumentException("Invalid file: " + e, e);
        }
        return new CommonsMultipartFile(fileItem);
    }

}
