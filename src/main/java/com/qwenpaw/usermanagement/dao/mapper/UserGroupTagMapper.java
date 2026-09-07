package com.qwenpaw.usermanagement.dao.mapper;

import com.qwenpaw.usermanagement.dao.entity.UserGroupTagDO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;

/**
 * 用户分群标签关联数据访问接口
 */
@Mapper
public interface UserGroupTagMapper {

    int insert(UserGroupTagDO record);

    int deleteByGroupId(@Param("groupId") String groupId);

    List<UserGroupTagDO> selectByGroupId(@Param("groupId") String groupId);

    List<UserGroupTagDO> selectByTagId(@Param("tagId") String tagId);
}
