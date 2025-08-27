package com.ruoyi.web.controller.manager.bigscreen;

import cn.hutool.core.util.StrUtil;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.redis.RedisCache;
import com.ruoyi.manager.domain.dto.BigScreenParam;
import com.ruoyi.manager.domain.vo.bigscreen.center.OrderAndEnterpriseInfoVo;
import com.ruoyi.manager.domain.vo.bigscreen.center.OrderAndEnterpriseVo;
import com.ruoyi.manager.domain.vo.bigscreen.center.OrderDetailVo;
import com.ruoyi.manager.service.IBigScreenService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/screen/bigScreen")
@CrossOrigin(origins = "*")
public class BigScreenController {

    @Autowired
    private RedisCache redisCache;

    @Autowired
    private IBigScreenService bigScreenService;



    /**
     * 中间- 订单或公司聚冗数据
     * @param bigScreenParam
     * @return
     */
    @RequestMapping("orderAndEnterprise")
    public AjaxResult orderAndEnterprise(BigScreenParam bigScreenParam){
        try {
            if(StrUtil.isEmpty(bigScreenParam.getCode())){
                return AjaxResult.error("请选择区域");
            }
            List<OrderAndEnterpriseVo> list = this.bigScreenService.returnOrderAndEnterprise(bigScreenParam);
            return AjaxResult.success(list);
        }catch (Exception e){
            return AjaxResult.error("数据异常, 请联系管理员");
        }
    }

    /**
     *
     * @param bigScreenParam
     * @return
     */
    @RequestMapping("orderAndEnterpriseInfo")
    public AjaxResult orderAndEnterpriseInfo(BigScreenParam bigScreenParam){
        try {
            if(null == bigScreenParam.getType() || StrUtil.isEmpty(bigScreenParam.getCode())){
                return AjaxResult.error("参数不存在");
            }
            List<OrderAndEnterpriseInfoVo> list = this.bigScreenService.orderAndEnterpriseInfo(bigScreenParam);
            return AjaxResult.success(list);
        }catch (Exception e){
            return AjaxResult.error("数据异常, 请联系管理员");
        }
    }


    /**
     *
     * @return
     */
    @RequestMapping("orderAndEnterpriseDetail")
    public AjaxResult orderAndEnterpriseDetail(BigScreenParam bigScreenParam){
        try {
            if(null == bigScreenParam.getType()){
                return AjaxResult.error("请求参数不存在");
            }
            OrderDetailVo orderDetailVo = new OrderDetailVo();
            if(1 == bigScreenParam.getType()){
                orderDetailVo = this.bigScreenService.returnOrderDetail(bigScreenParam);
            } else {
                String cacheObject = redisCache.getCacheObject("big_screen:enterprise_detail");
                if(StrUtil.isEmpty(cacheObject)){
                    redisCache.setCacheObject("big_screen:enterprise_detail", "");
                }
            }
            return AjaxResult.success(orderDetailVo);
        }catch (Exception e){
            return AjaxResult.error("数据异常, 请联系管理员");
        }
    }
}
