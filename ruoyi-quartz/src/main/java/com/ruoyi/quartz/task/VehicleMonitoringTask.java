package com.ruoyi.quartz.task;

import cn.hutool.json.JSONArray;
import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.ruoyi.base.domain.*;
import com.ruoyi.base.service.*;
import com.ruoyi.base.service.forest.HttpBaseInfoApiService;
import com.ruoyi.common.exception.ServiceException;
import lombok.extern.log4j.Log4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;
import java.util.List;

@Log4j
@Component("vehicleMonitoringTask")
public class VehicleMonitoringTask {

    @Resource
    private HttpBaseInfoApiService httpBaseInfoApiService;

    @Autowired
    private IOdsSzdnSectionService odsSzdnSectionService;
    @Autowired
    private IOdsYhglVBaseOrgService odsYhglVBaseOrgService;
    @Autowired
    private IOdsSzdnGantryService odsSzdnGantryService;
    @Autowired
    private IOdsSzdnTollService odsSzdnTollService;
    @Autowired
    private IDwdLcztSfzjcxxService dwdLcztSfzjcxxService;
    @Autowired
    private IDwdLcztFwqjcxxService dwdLcztFwqjcxxService;
    @Autowired
    private IDwdLcztSfsjcxxService dwdLcztSfsjcxxService;


    /**
     * 同步机构信息
     */
    @Transactional(rollbackFor = Exception.class)
    public void syncOrgInfo() {
        JSONObject jsonObject = httpBaseInfoApiService.getOrgInfoList();
        if (null == jsonObject || 200 != jsonObject.getInt("code")) {
            log.error("机构接口返回数据异常:" + jsonObject);
            return;
        }

        JSONArray jsonArray = (JSONArray) jsonObject.get("data");
        if (jsonArray.isEmpty()) {
            return;
        }

        List<OdsYhglVBaseOrg> list = JSONUtil.toList(jsonArray, OdsYhglVBaseOrg.class);

        this.odsYhglVBaseOrgService.truncateTable();
        this.odsYhglVBaseOrgService.saveBatch(list);
    }




    /**
     * 同步路段信息
     */
    @Transactional(rollbackFor = Exception.class)
    public void syncSectionInfo(){
        JSONObject jsonObject = httpBaseInfoApiService.getSectionInfoList();
        if (null == jsonObject || 200 != jsonObject.getInt("code")) {
            log.error("路段接口返回数据异常:" + jsonObject);
            return;
        }

        JSONArray jsonArray = (JSONArray) jsonObject.get("data");
        if(jsonArray.isEmpty()){
            return;
        }

        List<OdsSzdnSection> list = JSONUtil.toList(jsonArray, OdsSzdnSection.class);

        // 清空数据  mybatis-plus 安全机制 会对delete语句没有where条件的进行拦截
        // 抛出 Prohibition of full table deletion
        // 使用 注解 @Update  绕够MP的安全检测
        this.odsSzdnSectionService.truncateTable();
        // 全量新增数据
        this.odsSzdnSectionService.saveBatch(list);
    }





    /**
     * 同步门架信息
     */
    @Transactional(rollbackFor = Exception.class)
    public void syncGantryInfo(){
        JSONObject jsonObject = httpBaseInfoApiService.getGantryInfoList();
        if (null == jsonObject || 200 != jsonObject.getInt("code")) {
            log.error("门架接口返回数据异常:" + jsonObject);
            return;
        }

        JSONArray jsonArray = (JSONArray) jsonObject.get("data");
        if(jsonArray.isEmpty()){
            return;
        }

        List<OdsSzdnGantry> list = JSONUtil.toList(jsonArray, OdsSzdnGantry.class);

        this.odsSzdnGantryService.truncateTable();
        this.odsSzdnGantryService.saveBatch(list);
    }


    /**
     * 同步服务区信息
     */
    @Transactional(rollbackFor = Exception.class)
    public void syncServiceAreaInfoInfo(){
        JSONObject jsonObject = httpBaseInfoApiService.getServiceAreaInfoList();
        if (null == jsonObject || 200 != jsonObject.getInt("code")) {
            log.error("服务区接口返回数据异常:" + jsonObject);
            return;
        }

        JSONArray jsonArray = (JSONArray) jsonObject.get("data");
        if(jsonArray.isEmpty()){
            return;
        }

        List<DwdLcztFwqjcxx> list = JSONUtil.toList(jsonArray, DwdLcztFwqjcxx.class);

        this.dwdLcztFwqjcxxService.truncateTable();
        this.dwdLcztFwqjcxxService.saveBatch(list);
    }

    /**
     * 同步收费所信息
     */
    @Transactional(rollbackFor = Exception.class)
    public void syncTollBoothInfoInfo(){
        JSONObject jsonObject = httpBaseInfoApiService.getTollBoothInfoList();
        if (null == jsonObject || 200 != jsonObject.getInt("code")) {
            log.error("收费所接口返回数据异常:" + jsonObject);
            return;
        }

        JSONArray jsonArray = (JSONArray) jsonObject.get("data");
        if(jsonArray.isEmpty()){
            return;
        }

        List<DwdLcztSfsjcxx> list = JSONUtil.toList(jsonArray, DwdLcztSfsjcxx.class);

        this.dwdLcztSfsjcxxService.truncateTable();
        this.dwdLcztSfsjcxxService.saveBatch(list);
    }

    /**
     * 同步收费站基础信息位置
     */
    @Transactional(rollbackFor = Exception.class)
    public void syncSfzjcxxInfoInfo(){
        JSONObject jsonObject = httpBaseInfoApiService.getSfzjcxxInfoList();
        if (null == jsonObject || 200 != jsonObject.getInt("code")) {
            log.error("收费所位置接口返回数据异常:" + jsonObject);
            return;
        }

        JSONArray jsonArray = (JSONArray) jsonObject.get("data");
        if(jsonArray.isEmpty()){
            return;
        }

        List<DwdLcztSfzjcxx> list = JSONUtil.toList(jsonArray, DwdLcztSfzjcxx.class);

        this.dwdLcztSfzjcxxService.truncateTable();
        this.dwdLcztSfzjcxxService.saveBatch(list);
    }

    /**
     * 同步收费站信息
     */
    @Transactional(rollbackFor = Exception.class)
    public void syncTollStationInfo(){
        JSONObject jsonObject = httpBaseInfoApiService.getTollStationInfoList();
        if (null == jsonObject || 200 != jsonObject.getInt("code")) {
            log.error("收费站接口返回数据异常:" + jsonObject);
            return;
        }

        JSONArray jsonArray = (JSONArray) jsonObject.get("data");
        if(jsonArray.isEmpty()){
            return;
        }

        List<OdsSzdnToll> list = JSONUtil.toList(jsonArray, OdsSzdnToll.class);

        this.odsSzdnTollService.truncateTable();
        this.odsSzdnTollService.saveBatch(list);
    }



}
