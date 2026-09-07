package com.qwenpaw.usermanagement.dao.mapper;

import com.qwenpaw.usermanagement.dao.entity.TagDO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;

/**
 * 标签数据访问接口
 */
@Mapper
public interface TagMapper {

    int insert(TagDO record);

    int updateById(TagDO record);

    int deleteById(@Param("tagId") String tagId);

    TagDO selectById(@Param("tagId") String tagId);

    List<TagDO> selectAll();

    List<TagDO> selectByCategoryId(@Param("categoryId") String categoryId);

    List<TagDO> selectByParentId(@Param("parentId") Long parentId);

    int countByCategoryId(@Param("categoryId") String categoryId);
}
