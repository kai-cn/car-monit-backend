package com.ruoyi.common.utils;

import com.aliyun.mns.client.CloudAccount;
import com.aliyun.mns.client.CloudTopic;
import com.aliyun.mns.client.MNSClient;
import com.aliyun.mns.model.BatchSmsAttributes;
import com.aliyun.mns.model.MessageAttributes;
import com.aliyun.mns.model.RawTopicMessage;
import com.aliyun.mns.model.TopicMessage;
import com.aliyuncs.DefaultAcsClient;
import com.aliyuncs.IAcsClient;
import com.aliyuncs.dysmsapi.model.v20170525.SendSmsRequest;
import com.aliyuncs.dysmsapi.model.v20170525.SendSmsResponse;
import com.aliyuncs.http.MethodType;
import com.aliyuncs.profile.DefaultProfile;
import com.aliyuncs.profile.IClientProfile;
import lombok.extern.slf4j.Slf4j;

/**
 * 描述:阿里云短信服务工具类 phonenumber
 * **/
@Slf4j
public class AliyunSMSUtil {

	
	
	public void sendSMS(String singName,String templateCode,String mobile,String params,String accessKeyId,String accessKeySecret){
//		try{
//			IClientProfile profile = DefaultProfile.getProfile("cn-hangzhou", accessKeyId, accessKeySecret);
//	        DefaultProfile.addEndpoint("cn-hangzhou", "cn-hangzhou", "Sms",  "sms.aliyuncs.com");
//	        IAcsClient client = new DefaultAcsClient(profile);
//	        SingleSendSmsRequest request = new SingleSendSmsRequest();
//	        request.setSignName(singName);
//	        request.setTemplateCode(templateCode);
//	        request.setParamString(params);
//	        request.setRecNum(mobile);
////	        SingleSendSmsResponse httpResponse = client.getAcsResponse(request);
//	        client.getAcsResponse(request);
//		}catch(Exception e){
//			throw new RuntimeException(e);
//		}
	}
	
	public void sendSMSByMessage(String singName,String templateCode,String mobile,String paramsKey,String paramsValue,String accessKeyId,String accessKeySecret){
		MNSClient client = null;
		try{
		      CloudAccount account = new CloudAccount(accessKeyId, accessKeySecret, "http://1448889474882352.mns.cn-hangzhou.aliyuncs.com/");
		      client = account.getMNSClient();
		        CloudTopic topic = client.getTopicRef("ovuhr-sms-topic");
		        /**
		         * Step 2. set SMS message body ( required )
		         */
		        RawTopicMessage msg = new RawTopicMessage();
		        msg.setMessageBody("sms-message");
		        /**
		         * Step 3. generate SMS message attributes
		         */
		        MessageAttributes messageAttributes = new MessageAttributes();
		        BatchSmsAttributes batchSmsAttributes = new BatchSmsAttributes();
		        // 3.1 set SMS message sign name
		        batchSmsAttributes.setFreeSignName(singName);
		        // 3.2 set SMS message template code
		        batchSmsAttributes.setTemplateCode(templateCode);
		        // 3.3 set SMS message receiver param (defined in SMS message template)
		        BatchSmsAttributes.SmsReceiverParams smsReceiverParams = new BatchSmsAttributes.SmsReceiverParams();
		        smsReceiverParams.setParam(paramsKey, paramsValue);
		        // 3.4 add phone number of receiver (200 receivers at most)
		        batchSmsAttributes.addSmsReceiver(mobile, smsReceiverParams);
		       
		        messageAttributes.setBatchSmsAttributes(batchSmsAttributes);
		        TopicMessage ret = topic.publishMessage(msg, messageAttributes);
//	            System.out.println("MessageId: " + ret.getMessageId());
//	            System.out.println("MessageMD5: " + ret.getMessageBodyMD5());
		}catch(Exception e){
			throw new RuntimeException(e);
		}finally{
			try{
				if(client!=null){
					 client.close();
				}
			}catch(Exception e){
				throw new RuntimeException(e);
			}
		}
	}
	
	public int sendSMSByHttp(String singName,String templateCode,String mobile,String paramsKey,String paramsValue,String accessKeyId,String accessKeySecret){
		try{
			System.setProperty("sun.net.client.defaultConnectTimeout", "10000");
			System.setProperty("sun.net.client.defaultReadTimeout", "10000");
			//初始化ascClient需要的几个参数
			final String product = "Dysmsapi";//短信API产品名称（短信产品名固定，无需修改）
			final String domain = "dysmsapi.aliyuncs.com";//短信API产品域名（接口地址固定，无需修改）
			//初始化ascClient,暂时不支持多region（请勿修改）
			IClientProfile profile = DefaultProfile.getProfile("cn-hangzhou", accessKeyId,
			accessKeySecret);
			DefaultProfile.addEndpoint("cn-hangzhou", "cn-hangzhou", product, domain);
			IAcsClient acsClient = new DefaultAcsClient(profile);
			 //组装请求对象
			 SendSmsRequest request = new SendSmsRequest();
			 //使用post提交
			 request.setMethod(MethodType.POST);
			 //必填:待发送手机号。支持以逗号分隔的形式进行批量调用，批量上限为1000个手机号码,批量调用相对于单条调用及时性稍有延迟,验证码类型的短信推荐使用单条调用的方式
			 request.setPhoneNumbers(mobile);
			 //必填:短信签名-可在短信控制台中找到
			 request.setSignName(singName);
			 //必填:短信模板-可在短信控制台中找到
			 request.setTemplateCode(templateCode);
			 //可选:模板中的变量替换JSON串,如模板内容为"亲爱的${name},您的验证码为${code}"时,此处的值为
			 //友情提示:如果JSON中需要带换行符,请参照标准的JSON协议对换行符的要求,比如短信内容中包含\r\n的情况在JSON中需要表示成\\r\\n,否则会导致JSON在服务端解析失败
			 request.setTemplateParam("{\""+paramsKey+"\":\""+paramsValue+"\",\"product\":\"采购系统\"}");
			 //request.setTemplateParam("{\""+paramsKey+"\":\""+paramsValue+"\"}");
			 //可选-上行短信扩展码(扩展码字段控制在7位或以下，无特殊需求用户请忽略此字段)
			 //request.setSmsUpExtendCode("90997");
			 //可选:outId为提供给业务方扩展字段,最终在短信回执消息中将此值带回给调用者
			 request.setOutId("yourOutId");
			//请求失败这里会抛ClientException异常
			SendSmsResponse sendSmsResponse = acsClient.getAcsResponse(request);
			log.info("SMS SEND ERROR CODE:"+sendSmsResponse.getCode());
			if(sendSmsResponse.getCode() != null && sendSmsResponse.getCode().equals("OK")) {
				return 1;
			}else if(sendSmsResponse.getCode() != null && sendSmsResponse.getCode().indexOf("BUSINESS_LIMIT_CONTROL")>-1){
				return -1;
			}
			return 1;
		}catch(Exception e){
			throw new RuntimeException(e);
		}finally{
			try{
				
			}catch(Exception e){
				throw new RuntimeException(e);
			}
		}
	}

	public int sendSMSByHttp(String singName,String templateCode,String mobile,String params,String accessKeyId,String accessKeySecret){
		try{
			System.setProperty("sun.net.client.defaultConnectTimeout", "100000");
			System.setProperty("sun.net.client.defaultReadTimeout", "100000");
			//初始化ascClient需要的几个参数
			final String product = "Dysmsapi";//短信API产品名称（短信产品名固定，无需修改）
			final String domain = "dysmsapi.aliyuncs.com";//短信API产品域名（接口地址固定，无需修改）
			//初始化ascClient,暂时不支持多region（请勿修改）
			IClientProfile profile = DefaultProfile.getProfile("cn-hangzhou", accessKeyId,
					accessKeySecret);
			DefaultProfile.addEndpoint("cn-hangzhou", "cn-hangzhou", product, domain);
			IAcsClient acsClient = new DefaultAcsClient(profile);
			//组装请求对象
			SendSmsRequest request = new SendSmsRequest();
			//使用post提交
			request.setMethod(MethodType.POST);
			//必填:待发送手机号。支持以逗号分隔的形式进行批量调用，批量上限为1000个手机号码,批量调用相对于单条调用及时性稍有延迟,验证码类型的短信推荐使用单条调用的方式
			request.setPhoneNumbers(mobile);
			//必填:短信签名-可在短信控制台中找到
			request.setSignName(singName);
			//必填:短信模板-可在短信控制台中找到
			request.setTemplateCode(templateCode);
			//可选:模板中的变量替换JSON串,如模板内容为"亲爱的${name},您的验证码为${code}"时,此处的值为
			//友情提示:如果JSON中需要带换行符,请参照标准的JSON协议对换行符的要求,比如短信内容中包含\r\n的情况在JSON中需要表示成\\r\\n,否则会导致JSON在服务端解析失败
			request.setTemplateParam(params);
			//request.setTemplateParam("{\""+paramsKey+"\":\""+paramsValue+"\"}");
			//可选-上行短信扩展码(扩展码字段控制在7位或以下，无特殊需求用户请忽略此字段)
			//request.setSmsUpExtendCode("90997");
			//可选:outId为提供给业务方扩展字段,最终在短信回执消息中将此值带回给调用者
			request.setOutId("yourOutId");
			//请求失败这里会抛ClientException异常
			SendSmsResponse sendSmsResponse = acsClient.getAcsResponse(request);
			log.info("SMS SEND ERROR CODE:"+sendSmsResponse.getCode());
			if(sendSmsResponse.getCode() != null && sendSmsResponse.getCode().equals("OK")) {
				return 1;
			}else{
				throw new RuntimeException("send sms error code:"+sendSmsResponse.getCode()+" message:"+sendSmsResponse.getMessage());
			}
		}catch(RuntimeException e){
			throw e;
		}catch(Exception e){
			throw new RuntimeException(e);
		}finally{
			try{

			}catch(Exception e){
				throw new RuntimeException(e);
			}
		}
	}

	public static void main(String[] args){
		// 本地手动验证入口：凭据一律从环境变量读取，禁止在源码中内置任何 AccessKey。
		String akId = System.getenv("ALIYUN_SMS_ACCESS_KEY_ID");
		String akSecret = System.getenv("ALIYUN_SMS_ACCESS_KEY_SECRET");
		if (akId == null || akSecret == null || akId.isEmpty() || akSecret.isEmpty()) {
			System.out.println("请设置环境变量 ALIYUN_SMS_ACCESS_KEY_ID / ALIYUN_SMS_ACCESS_KEY_SECRET 后再运行");
			return;
		}
		try{
			AliyunSMSUtil sms = new AliyunSMSUtil();
			String params = "{\"code\":\"123456\",\"product\":\"采购系统\"}";
			sms.sendSMSByHttp("大鱼测试","SMS_211990318","13476252626",params,akId,akSecret);
		}catch(Exception e){
			e.printStackTrace();
		}
	}
	
}
