package com.ruoyi.base.service.forest;

import com.alibaba.fastjson2.JSONObject;
import com.dtflys.forest.annotation.*;
import com.ruoyi.base.domain.PathQueryRo;

/**
 * @Description: 路网路径接口信息
 * @author zhukai
 * @date 2025/11/20 11:14
 * @Param:
 * @return:
 */
public interface RoadPathApi {

	@Headers({ "Connection:close"})
	@Post(url = "${roadPathUrl}/api/routes/query", connectTimeout = 30000)
	public JSONObject getRoadPath(@JSONBody PathQueryRo queryRo);
}
