package com.ruoyi.manager.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.manager.domain.vo.bigscreen.CarAuditVO;
import com.ruoyi.manager.domain.vo.bigscreen.CarStatisticsVO;
import com.ruoyi.manager.mapper.CarConfimFreeMapper;
import com.ruoyi.manager.domain.CarConfimFree;
import com.ruoyi.manager.service.ICarConfimFreeService;
import com.ruoyi.system.service.ISysDictDataService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.CollectionUtils;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 确认补缴Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-28
 */
@Service
public class CarConfimFreeServiceImpl extends ServiceImpl<CarConfimFreeMapper, CarConfimFree> implements ICarConfimFreeService {

    @Autowired
    private CarConfimFreeMapper carConfimFreeMapper;
    @Autowired
    private ISysDictDataService sysDictDataService;

    /**
     * 查询确认补缴
     *
     * @param id 确认补缴ID
     * @return 确认补缴
     */
    @Override
    public CarConfimFree selectCarConfimFreeById(String id) {
        return carConfimFreeMapper.selectCarConfimFreeById(id);
    }

    /**
     * 查询确认补缴列表
     *
     * @param carConfimFree 确认补缴
     * @return 确认补缴
     */
    @Override
    public List<CarConfimFree> selectCarConfimFreeList(CarConfimFree carConfimFree) {
        return carConfimFreeMapper.selectCarConfimFreeList(carConfimFree);
    }


    /**
     * 新增或者修改确认补缴
     *
     * @param carConfimFree 确认补缴
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveCarConfimFree(CarConfimFree carConfimFree) {
        if (CommonUtil.isNotBlank(carConfimFree.getId())) {
            // 修改
            carConfimFreeMapper.updateById(carConfimFree);
        } else {
            // 新增 主键
            carConfimFreeMapper.insert(carConfimFree);
        }
        return AjaxResult.success("操作成功！", carConfimFree.getId());
    }

    /**
     * 批量删除确认补缴
     *
     * @param ids 需要删除的确认补缴ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteCarConfimFreeByIds(String[] ids) {
        int count = carConfimFreeMapper.deleteCarConfimFreeByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除确认补缴信息
     *
     * @param id 确认补缴ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteCarConfimFreeById(String id) {
        int count = carConfimFreeMapper.deleteCarConfimFreeById(id);
        return AjaxResult.success(count);
    }

    @Override
    public List<CarStatisticsVO> getCarStatistics() {
        // 逃费类型
        Map<String, String> escapedTypeMap = sysDictDataService.selectDictDataMap("escaped_type");
        List<CarStatisticsVO> list = carConfimFreeMapper.getCarStatistics();
        Map<String, CarStatisticsVO> voMap = list.stream().collect(Collectors.toMap(CarStatisticsVO::getEscapedType, v -> v));
        List<CarStatisticsVO> res = new ArrayList<>();
        escapedTypeMap.forEach((k, v) -> {
            CarStatisticsVO vo = new CarStatisticsVO();
            res.add(vo);
            vo.setEscapedType(k);
            vo.setEscapedTypeName(v);
            CarStatisticsVO vo1 = voMap.get(k);
            if (vo1 != null) {
                vo.setNumber(vo1.getNumber());
                vo.setEscapedAmount(vo1.getEscapedAmount());
            }
        });
        return res;
    }

    @Override
    public BigDecimal getCarConfirm() {
        return carConfimFreeMapper.getCarConfirm();
    }
}
