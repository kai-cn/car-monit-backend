package com.ruoyi.system.service.impl;

import com.ruoyi.common.utils.AliyunSMSUtil;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.system.service.SMSService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

@Slf4j
@Service
public class SMSServiceImpl implements SMSService {

    @Value("${sms.signature}")
    private String signature = null;

    @Value("${sms.accessKeyId}")
    private String accessKeyId = null;

    @Value("${sms.accessKeySecret}")
    private String accessKeySecret = null;

    @Value("${sms.sendCodeTemplete}")
    private String codeTemplete = null;

    @Value("${sms.sendCheckPersonNoticeTemplete}")
    private String sendCheckPersonNoticeTemplete = null;

    @Value("${sms.sendExpertNoticeTemplete}")
    private String sendExpertNoticeTemplete = null;

    @Value("${sms.sendInvitationSupplierTemplate}")
    private String sendInvitationSupplierTemplate;

//    @Value("${sms.sendSupplierInvitationsNoticeTemplete}")
    private String sendSupplierInvitationsNoticeTemplete = null;

    @Value("${sms.sendYckbSupplierTemplate}")
    private String sendYckbSupplierTemplate;


    @Override
    public void sendCode(String code, String mobile) {
        if(mobile.indexOf("SMS_")>-1){return;}
        AliyunSMSUtil sms = new AliyunSMSUtil();
        String params = "{\"code\":\""+code+"\"}";
        sms.sendSMSByHttp(signature,codeTemplete,mobile,params,accessKeyId,accessKeySecret);
    }

    @Async
    @Override
    public void sendExpertNotice(String mobile, String name, String company, String projectName, String address, String date, String code) {
        AliyunSMSUtil sms = new AliyunSMSUtil();
        String params = "{\"name\":\""+name+"\",\"company\":\""+company+"\",\"project\":\""+projectName+"\",\"address\":\""+address+"\",\"date\":\""+date+"\",\"code\":\""+code+"\"}";
        System.out.println("mobile:"+mobile+" "+code+" "+name);
        sms.sendSMSByHttp(signature,sendExpertNoticeTemplete,mobile,params,accessKeyId,accessKeySecret);
    }

    /**
     * 发送供应商邀请短信
     * @param phone
     * @param paramJsonStr
     */
    @Async
    @Override
    public void sendInvitationSupplier(String phone, String paramJsonStr) {
        if (StringUtils.isNotBlank(phone) &&
            StringUtils.isNotBlank(paramJsonStr) &&
            StringUtils.isNotBlank(sendInvitationSupplierTemplate)) {

            AliyunSMSUtil sms = new AliyunSMSUtil();
            sms.sendSMSByHttp(signature, sendInvitationSupplierTemplate, phone, paramJsonStr, accessKeyId, accessKeySecret);

            log.info("发送供应商邀请短信成功! 参数: phone: {}, paramJsonStr: {}, sendInvitationSupplierTemplate: {}", phone, paramJsonStr, sendInvitationSupplierTemplate);
        } else {
            log.error("发送供应商邀请短信失败! 参数缺失! 参数: phone: {}, paramJsonStr: {}, sendInvitationSupplierTemplate: {}", phone, paramJsonStr, sendInvitationSupplierTemplate);
        }
    }

    @Override
    public void sendYckbSupplier(String phone, String paramJsonStr) {
        if (StringUtils.isNotBlank(phone) &&
                StringUtils.isNotBlank(paramJsonStr) &&
                StringUtils.isNotBlank(sendYckbSupplierTemplate)) {

            AliyunSMSUtil sms = new AliyunSMSUtil();
            sms.sendSMSByHttp(signature, sendYckbSupplierTemplate, phone, paramJsonStr, accessKeyId, accessKeySecret);

            log.info("发送供应商邀请短信成功! 参数: phone: {}, paramJsonStr: {}, sendYckbSupplierTemplate: {}", phone, paramJsonStr, sendYckbSupplierTemplate);
        } else {
            log.error("发送供应商邀请短信失败! 参数缺失! 参数: phone: {}, paramJsonStr: {}, sendYckbSupplierTemplate: {}", phone, paramJsonStr, sendYckbSupplierTemplate);
        }
    }

    @Async
    @Override
    public void sendCheckPersonNotice(String mobile, String name, String company, String projectName, String address, String date) {
//        System.out.println("sendCheckPersonNotice....");
        AliyunSMSUtil sms = new AliyunSMSUtil();
        String params = "{\"name\":\""+name+"\",\"company\":\""+company+"\",\"project\":\""+projectName+"\",\"address\":\""+address+"\",\"date\":\""+date+"\"}";
        sms.sendSMSByHttp(signature,sendCheckPersonNoticeTemplete,mobile,params,accessKeyId,accessKeySecret);
    }

    @Async
    @Override
    public void sendSupplierInvitationsNotice(String mobile, String name, String company, String projectName, String address, String date) {
        AliyunSMSUtil sms = new AliyunSMSUtil();
        String params = "{\"name\":\""+name+"\",\"company\":\""+company+"\",\"project\":\""+projectName+"\",\"address\":\""+address+"\",\"date\":\""+date+"\"}";
        sms.sendSMSByHttp(signature,sendSupplierInvitationsNoticeTemplete,mobile,params,accessKeyId,accessKeySecret);
    }

}
