package com.ruoyi.system.service.forest;

import com.dtflys.forest.annotation.GetRequest;
import com.dtflys.forest.annotation.Var;

import java.io.InputStream;

public interface FileApi {

    /**
     * 返回类型用byte[]，可将下载的文件转换成字节数组
     */
    @GetRequest(url = "{URL}")
    byte[] downloadImageToByteArray(@Var("URL") String URL);

    /**
     * 返回类型用InputStream，用流的方式读取文件内容
     */
    @GetRequest(url = "{URL}")
    InputStream downloadImageToInputStream(@Var("URL") String URL);
}
