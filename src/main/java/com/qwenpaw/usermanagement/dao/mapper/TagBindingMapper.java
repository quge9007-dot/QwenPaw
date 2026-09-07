package com.qwenpaw.usermanagement.dao.mapper;

import com.qwenpaw.usermanagement.dao.entity.TagBindingDO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;

/**
 * 标签绑定数据访问接口
 */
@Mapper
public interface TagBindingMapper {

    int insert(TagBindingDO record);

    int deleteByUserIdAndTagId(@Param("userId") String userId, @Param("tagId") String tagId);

    TagBindingDO selectByUserIdAndTagId(@Param("userId") String userId, @Param("tagId") String tagId);

    List<TagBindingDO> selectByUserId(@Param("userId") String userId);

    List<TagBindingDO> selectByTagId(@Param("tagId") String tagId);

    int countByTagId(@Param("tagId") String tagId);
}
