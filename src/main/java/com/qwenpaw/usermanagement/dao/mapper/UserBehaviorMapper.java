package com.qwenpaw.usermanagement.dao.mapper;

import com.qwenpaw.usermanagement.dao.entity.UserBehaviorDO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;

/**
 * 用户行为数据访问接口
 */
@Mapper
public interface UserBehaviorMapper {

    int insert(UserBehaviorDO record);

    List<UserBehaviorDO> selectByUserId(@Param("userId") String userId);

    List<UserBehaviorDO> selectByBehaviorType(@Param("behaviorType") String behaviorType);
}
