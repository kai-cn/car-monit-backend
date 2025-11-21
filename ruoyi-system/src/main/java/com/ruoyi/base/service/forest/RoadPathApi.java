package com.ruoyi.base.service.forest;

import com.alibaba.fastjson2.JSONObject;
import com.dtflys.forest.annotation.BaseRequest;
import com.dtflys.forest.annotation.JSONBody;
import com.dtflys.forest.annotation.Post;
import com.ruoyi.base.domain.PathQueryRo;

/**
 * @Description: 路网路径接口信息
 * @author zhukai
 * @date 2025/11/20 11:14
 * @Param:
 * @return:
 */
@BaseRequest(baseURL = "#{roadPathUrl}")
public interface RoadPathApi {

	@Post(url = "/api/routes/query")
	public JSONObject getRoadPath(@JSONBody PathQueryRo queryRo);
}
