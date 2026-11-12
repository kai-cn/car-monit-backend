package com.ruoyi.web.util;

import org.springframework.web.multipart.MultipartFile;

import java.io.*;
import java.util.Base64;

/**
 * base64转为multipartFile工具类
 *
 */

public class Base64DecodeMultipartFile implements MultipartFile {
    private final byte[] imgContent;
    private final String header;

    public Base64DecodeMultipartFile(byte[] imgContent, String header) {
        this.imgContent = imgContent;
        this.header = header.split(";")[0];
    }

    @Override
    public String getName() {
        return System.currentTimeMillis() + Math.random() + "." + header.split("/")[1];
    }

    @Override
    public String getOriginalFilename() {
        return System.currentTimeMillis() + (int) Math.random() * 10000 + "." + header.split("/")[1];
    }

    @Override
    public String getContentType() {
        return header.split(":")[1];
    }

    @Override
    public boolean isEmpty() {
        return imgContent == null || imgContent.length == 0;
    }

    @Override
    public long getSize() {
        return imgContent.length;
    }

    @Override
    public byte[] getBytes() throws IOException {
        return imgContent;
    }

    @Override
    public InputStream getInputStream() throws IOException {
        return new ByteArrayInputStream(imgContent);
    }

    @Override
    public void transferTo(File dest) throws IOException, IllegalStateException {
        new FileOutputStream(dest).write(imgContent);
    }

    /**
     * base64转multipartFile
     *
     * @param base64
     * @return
     */
    public static MultipartFile base64Convert(String base64) {
        String[] baseStrs = base64.split(",");

        // JDK 9 起 sun.misc.BASE64Decoder 不可访问；getMimeDecoder 与旧实现同样容忍
        // 换行/空白等非 base64 字符，保持上传 data URI 的兼容行为。
        // 旧代码对 byte[] 逐元素 += 256 属于复合赋值隐式窄化，实际不改变任何字节，已移除。
        byte[] b;
        try {
            b = Base64.getMimeDecoder().decode(baseStrs[1]);
        } catch (IllegalArgumentException e) {
            b = new byte[0];
        }
        return new Base64DecodeMultipartFile(b, baseStrs[0]);
    }
}