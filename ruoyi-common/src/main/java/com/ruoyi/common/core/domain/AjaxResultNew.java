package com.ruoyi.common.core.domain;

import com.ruoyi.common.constant.HttpStatus;
import com.ruoyi.common.utils.StringUtils;

import java.util.HashMap;
import java.util.Objects;

/**
 * 操作消息提醒
 * 
 * @author ruoyi
 * @param <T> 数据泛型
 */
public class AjaxResultNew<T> extends HashMap<String, Object>
{
    private static final long serialVersionUID = 1L;

    /** 状态码 */
    public static final String CODE_TAG = "code";

    /** 返回内容 */
    public static final String MSG_TAG = "msg";

    /** 数据对象 */
    public static final String DATA_TAG = "data";

    /**
     * 初始化一个新创建的 AjaxResult 对象，使其表示一个空消息。
     */
    public AjaxResultNew()
    {
    }

    /**
     * 初始化一个新创建的 AjaxResult 对象
     *
     * @param code 状态码
     * @param msg 返回内容
     */
    public AjaxResultNew(int code, String msg)
    {
        super.put(CODE_TAG, code);
        super.put(MSG_TAG, msg);
    }

    /**
     * 初始化一个新创建的 AjaxResult 对象
     *
     * @param code 状态码
     * @param msg 返回内容
     * @param data 数据对象
     */
    public AjaxResultNew(int code, String msg, T data)
    {
        super.put(CODE_TAG, code);
        super.put(MSG_TAG, msg);
        if (StringUtils.isNotNull(data))
        {
            super.put(DATA_TAG, data);
        }
    }

    /**
     * 返回成功消息
     * 
     * @param <T> 数据泛型
     * @return 成功消息
     */
    public static <T> AjaxResultNew<T> success()
    {
        return AjaxResultNew.<T>success("操作成功");
    }

    /**
     * 返回成功数据
     * 
     * @param data 数据对象
     * @param <T> 数据泛型
     * @return 成功消息
     */
    public static <T> AjaxResultNew<T> success(T data)
    {
        return AjaxResultNew.<T>success("操作成功", data);
    }

    /**
     * 返回成功消息
     * 
     * @param msg 返回内容
     * @param <T> 数据泛型
     * @return 成功消息
     */
    public static <T> AjaxResultNew<T> success(String msg)
    {
        return AjaxResultNew.<T>success(msg, null);
    }

    /**
     * 返回成功消息
     * 
     * @param msg 返回内容
     * @param data 数据对象
     * @param <T> 数据泛型
     * @return 成功消息
     */
    public static <T> AjaxResultNew<T> success(String msg, T data)
    {
        return new AjaxResultNew<>(HttpStatus.SUCCESS, msg, data);
    }

    /**
     * 返回警告消息
     *
     * @param msg 返回内容
     * @param <T> 数据泛型
     * @return 警告消息
     */
    public static <T> AjaxResultNew<T> warn(String msg)
    {
        return AjaxResultNew.<T>warn(msg, null);
    }

    /**
     * 返回警告消息
     *
     * @param msg 返回内容
     * @param data 数据对象
     * @param <T> 数据泛型
     * @return 警告消息
     */
    public static <T> AjaxResultNew<T> warn(String msg, T data)
    {
        return new AjaxResultNew<>(HttpStatus.WARN, msg, data);
    }

    /**
     * 返回错误消息
     * 
     * @param <T> 数据泛型
     * @return 错误消息
     */
    public static <T> AjaxResultNew<T> error()
    {
        return AjaxResultNew.<T>error("操作失败");
    }

    /**
     * 返回错误消息
     * 
     * @param msg 返回内容
     * @param <T> 数据泛型
     * @return 错误消息
     */
    public static <T> AjaxResultNew<T> error(String msg)
    {
        return AjaxResultNew.<T>error(msg, null);
    }

    /**
     * 返回错误消息
     * 
     * @param msg 返回内容
     * @param data 数据对象
     * @param <T> 数据泛型
     * @return 错误消息
     */
    public static <T> AjaxResultNew<T> error(String msg, T data)
    {
        return new AjaxResultNew<>(HttpStatus.ERROR, msg, data);
    }

    /**
     * 返回错误消息
     * 
     * @param code 状态码
     * @param msg 返回内容
     * @param <T> 数据泛型
     * @return 错误消息
     */
    public static <T> AjaxResultNew<T> error(int code, String msg)
    {
        return new AjaxResultNew<>(code, msg, null);
    }

    /**
     * 是否为成功消息
     *
     * @return 结果
     */
    public boolean isSuccess()
    {
        return Objects.equals(HttpStatus.SUCCESS, this.get(CODE_TAG));
    }

    /**
     * 是否为警告消息
     *
     * @return 结果
     */
    public boolean isWarn()
    {
        return Objects.equals(HttpStatus.WARN, this.get(CODE_TAG));
    }

    /**
     * 是否为错误消息
     *
     * @return 结果
     */
    public boolean isError()
    {
        return Objects.equals(HttpStatus.ERROR, this.get(CODE_TAG));
    }

    /**
     * 方便链式调用
     *
     * @param key 键
     * @param value 值
     * @return 数据对象
     */
    @Override
    public AjaxResultNew<T> put(String key, Object value)
    {
        super.put(key, value);
        return this;
    }
}
