package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.spring.service.impl.ServiceImpl;
import com.ruoyi.base.domain.Geometry;
import com.ruoyi.base.mapper.GeometryMapper;
import com.ruoyi.base.service.IGeometryService;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.redis.RedisCache;
import com.ruoyi.common.utils.CommonUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 车辆信息Service业务层处理
 *
 * @author ruoyi
 * @date 2025-09-27
 */
@Service
public class GeometryServiceImpl extends ServiceImpl<GeometryMapper, Geometry> implements IGeometryService {

    @Autowired
    private GeometryMapper geometryMapper;

    @Autowired
    private RedisCache redisCache;

    /**
     * 查询车辆信息
     *
     * @param ID 车辆信息ID
     * @return 车辆信息
     */
    @Override
    public Geometry selectGeometryById(Integer ID) {
        return geometryMapper.selectGeometryById(ID);
    }

    /**
     * 查询车辆信息列表
     *
     * @param geometry 车辆信息
     * @return 车辆信息
     */
    @Override
    public List<Geometry> selectGeometryList(Geometry geometry) {
        return geometryMapper.selectGeometryList(geometry);
    }


    /**
     * 新增或者修改车辆信息
     *
     * @param geometry 车辆信息
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveGeometry(Geometry geometry)
    {
        if (null != geometry.getId())
        {
            // 修改
            geometryMapper.updateById(geometry);
        }
        else
        {
            // 新增 主键
            geometryMapper.insert(geometry);
        }
        this.updateRedisList();
        return AjaxResult.success("操作成功！",geometry.getId());
    }

    /**
     * 批量删除车辆信息
     *
     * @param IDs 需要删除的车辆信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteGeometryByIds(Integer[] IDs)
    {
        int count = geometryMapper.deleteGeometryByIds(IDs);
        return AjaxResult.success(count);
    }

    /**
     * 删除车辆信息信息
     *
     * @param ID 车辆信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteGeometryById(Integer ID)
    {
        int count = geometryMapper.deleteGeometryById(ID);
        return AjaxResult.success(count);
    }


    /**
     * 跟新缓存
     */
    public  List<Geometry> updateRedisList() {
        Geometry ceometry = new Geometry();
        ceometry.setLxfx("1");
        List<Geometry> list = geometryMapper.selectGeometryList(ceometry); // 查询的值
        List<Geometry> rtnlist = new ArrayList<>(); // 返回的值

        for (Geometry rtn:list){
            String roadCode =  CommonUtil.isNull(rtn.getLxbh()); // 路线编号
            String pileno = CommonUtil.isNull(rtn.getPaths()); // 桩号
            rtn.setLxbh(roadCode);
            if (CommonUtil.isNotBlank(roadCode) && CommonUtil.isNotBlank(pileno)){
                rtnlist.add(rtn);
            }
        }
        redisCache.setCacheObject(Constants.lxbh_jdwd, rtnlist);
        return list;
    }


    /**
     * 从缓存拿到carlist
     */
    public Map<String, List<Geometry>> getRedisList() {
        Map<String, List<Geometry>> map = new HashMap<>();
        List<Geometry> list = null;
        Object obj = redisCache.getCacheObject(Constants.lxbh_jdwd);
        if (null != obj) {
            list = (List) obj;
        } else {
            list = this.updateRedisList();
        }
        // 按照路线编号分组-----------------
        if (null !=list && list.size() > 0){
            map =  list.stream().collect(Collectors.groupingBy(Geometry::getLxbh));
        }
        return  map;
    }

    /**
     * 根据路线code 查询
     */
    public List<Geometry> getListByCode(List<String> roadCodeList) {
        List<Geometry> rtnlist = new ArrayList<Geometry>();
       /* for (String roadCode:roadCodeList){
            roadCode = CommonUtil.isNull(roadCode);
            if (CommonUtil.isNotBlank(roadCode)){
                 String points = redisCache.getCacheObject(Constants.lxbh_jdwd + roadCode);
                 if (CommonUtil.isNotBlank(points)){
                     Geometry addBo  = new Geometry();
                     addBo.setLxbh(roadCode);
                     addBo.setPaths(points);
                     rtnlist.add(addBo);
                 }
            }
        }*/
        return rtnlist;
    }

    /**
     * 查询未同步的路线
     *
     * @return
     */
    @Override
    public List<Geometry> syncAllGeometry() {
        return geometryMapper.syncAllGeometry();
    }
}
