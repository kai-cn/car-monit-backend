package com.ruoyi.common.utils;


import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.Objects;

import com.ruoyi.common.exception.CustomException;
import org.apache.commons.fileupload.FileItem;
import org.apache.commons.fileupload.FileItemFactory;
import org.apache.commons.fileupload.disk.DiskFileItem;
import org.apache.commons.fileupload.disk.DiskFileItemFactory;
import org.apache.commons.io.IOUtils;
import org.springframework.web.multipart.MultipartFile;

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
            return new FileItemMultipartFile(item);
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
        return new FileItemMultipartFile(fileItem);
    }

    /**
     * Spring Framework 6 起移除了 {@code CommonsMultipartFile}（commons-fileupload 1.x 适配器），
     * 这里直接适配 commons-fileupload 的 {@link FileItem} 到 {@link MultipartFile} 接口，
     * 保持原有“内存/磁盘 FileItem 转 MultipartFile”的能力不变。
     */
    private static final class FileItemMultipartFile implements MultipartFile {

        private final FileItem fileItem;

        private FileItemMultipartFile(FileItem fileItem) {
            this.fileItem = fileItem;
        }

        @Override
        public String getName() {
            return fileItem.getFieldName();
        }

        @Override
        public String getOriginalFilename() {
            return fileItem.getName();
        }

        @Override
        public String getContentType() {
            return fileItem.getContentType();
        }

        @Override
        public boolean isEmpty() {
            return fileItem.getSize() == 0L;
        }

        @Override
        public long getSize() {
            return fileItem.getSize();
        }

        @Override
        public byte[] getBytes() throws IOException {
            return fileItem.get();
        }

        @Override
        public InputStream getInputStream() throws IOException {
            return fileItem.getInputStream();
        }

        @Override
        public void transferTo(File dest) throws IOException {
            try {
                fileItem.write(dest);
            } catch (Exception e) {
                throw new IOException("写入目标文件失败: " + dest, e);
            }
        }
    }

}
