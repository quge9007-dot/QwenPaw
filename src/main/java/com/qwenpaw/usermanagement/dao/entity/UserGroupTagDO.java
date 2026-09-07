package com.qwenpaw.usermanagement.dao.entity;

import com.qwenpaw.usermanagement.common.model.BaseEntity;

/**
 * 用户分群标签关联数据对象
 */
public class UserGroupTagDO extends BaseEntity {

    private String groupId;
    private String tagId;
    private Integer matchMode;
    private Integer sortOrder;

    public String getGroupId() {
        return groupId;
    }

    public void setGroupId(String groupId) {
        this.groupId = groupId;
    }

    public String getTagId() {
        return tagId;
    }

    public void setTagId(String tagId) {
        this.tagId = tagId;
    }

    public Integer getMatchMode() {
        return matchMode;
    }

    public void setMatchMode(Integer matchMode) {
        this.matchMode = matchMode;
    }

    public Integer getSortOrder() {
        return sortOrder;
    }

    public void setSortOrder(Integer sortOrder) {
        this.sortOrder = sortOrder;
    }
}
