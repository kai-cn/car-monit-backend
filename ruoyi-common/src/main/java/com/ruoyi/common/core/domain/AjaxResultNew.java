package com.ruoyi.common.core.domain;

import com.ruoyi.common.constant.HttpStatus;
import com.ruoyi.common.utils.StringUtils;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;
import lombok.experimental.Accessors;

import java.io.Serializable;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

/**
 * 操作消息提醒
 *
 * @param <T> 数据泛型
 * @author ruoyi
 */
@Data
@ApiModel
@Accessors(chain = true)
public class AjaxResultNew<T> implements Serializable {
    private static final long serialVersionUID = 1L;
    public static final int STATUS_CODE_OK = 200;
    public static final int STATUS_CODE_ERROR = 500;

    @ApiModelProperty("状态码")
    private int code;

    @ApiModelProperty("返回内容")
    private String msg;

    @ApiModelProperty("返回数据")
    private T data;

    /**
     * 初始化一个新创建的 AjaxResult 对象，使其表示一个空消息。
     */
    public AjaxResultNew() {
        this.code = HttpStatus.SUCCESS;
        this.msg = "操作成功";
    }

    /**
     * 初始化一个新创建的 AjaxResult 对象
     *
     * @param code 状态码
     * @param msg  返回内容
     */
    public AjaxResultNew(int code, String msg) {
        this.code = code;
        this.msg = msg;
    }

    /**
     * 初始化一个新创建的 AjaxResult 对象
     *
     * @param code 状态码
     * @param msg  返回内容
     * @param data 数据对象
     */
    public AjaxResultNew(int code, String msg, T data) {
        this.code = code;
        this.msg = msg;
        this.data = data;
    }

    /**
     * 返回成功消息
     *
     * @param <T> 数据泛型
     * @return 成功消息
     */
    public static <T> AjaxResultNew<T> success() {
        return AjaxResultNew.success("操作成功");
    }

    /**
     * 返回成功数据
     *
     * @param data 数据对象
     * @param <T>  数据泛型
     * @return 成功消息
     */
    public static <T> AjaxResultNew<T> success(T data) {
        return AjaxResultNew.success("操作成功", data);
    }

    /**
     * 返回成功消息
     *
     * @param msg 返回内容
     * @param <T> 数据泛型
     * @return 成功消息
     */
    public static <T> AjaxResultNew<T> success(String msg) {
        return AjaxResultNew.success(msg, null);
    }

    /**
     * 返回成功消息
     *
     * @param msg  返回内容
     * @param data 数据对象
     * @param <T>  数据泛型
     * @return 成功消息
     */
    public static <T> AjaxResultNew<T> success(String msg, T data) {
        AjaxResultNew<T> result = new AjaxResultNew<>();
        result.setCode(STATUS_CODE_OK);
        result.setData(data);
        result.setMsg(msg);
        return result;
    }


    /**
     * 返回错误消息
     *
     * @param <T> 数据泛型
     * @return 错误消息
     */
    public static <T> AjaxResultNew<T> error() {
        return AjaxResultNew.error("操作失败");
    }

    /**
     * 返回错误消息
     *
     * @param msg 返回内容
     * @param <T> 数据泛型
     * @return 错误消息
     */
    public static <T> AjaxResultNew<T> error(String msg) {
        return AjaxResultNew.error(msg, null);
    }

    /**
     * 返回错误消息
     *
     * @param msg  返回内容
     * @param data 数据对象
     * @param <T>  数据泛型
     * @return 错误消息
     */
    public static <T> AjaxResultNew<T> error(String msg, T data) {
        return new AjaxResultNew<>(HttpStatus.ERROR, msg, data);
    }

    /**
     * 返回错误消息
     *
     * @param code 状态码
     * @param msg  返回内容
     * @param <T>  数据泛型
     * @return 错误消息
     */
    public static <T> AjaxResultNew<T> error(int code, String msg) {
        return new AjaxResultNew<>(code, msg, null);
    }



}
