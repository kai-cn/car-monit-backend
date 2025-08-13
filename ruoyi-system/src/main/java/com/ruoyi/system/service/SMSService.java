package com.ruoyi.system.service;

public interface SMSService {

    public void sendCode(String code, String mobile);

    public void sendCheckPersonNotice(String mobile, String name, String purchaser, String projectName, String address, String date);

    public void sendSupplierInvitationsNotice(String mobile, String name, String purchaser, String projectName, String address, String date);

    public void sendExpertNotice(String mobile, String name, String purchaser, String projectName, String address, String date, String url);

    /**
     * 发送供应商邀请短信
     * @param phone
     * @param paramJsonStr
     */
    void sendInvitationSupplier(String phone, String paramJsonStr);

    //延迟开标 发送供应商延迟开标通知短信
    void sendYckbSupplier(String phone, String paramJsonStr);

}
