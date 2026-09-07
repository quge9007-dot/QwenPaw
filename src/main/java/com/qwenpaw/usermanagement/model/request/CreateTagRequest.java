package com.qwenpaw.usermanagement.model.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/**
 * 创建标签请求
 */
public class CreateTagRequest {

    @NotBlank(message = "标签名称不能为空")
    @Size(max = 128, message = "标签名称长度不能超过128")
    private String tagName;

    @NotBlank(message = "标签编码不能为空")
    @Size(max = 64, message = "标签编码长度不能超过64")
    private String tagCode;

    @NotBlank(message = "分类ID不能为空")
    private String categoryId;

    private Long parentId;

    private Integer tagLevel;

    private Integer sortOrder;

    public String getTagName() {
        return tagName;
    }

    public void setTagName(String tagName) {
        this.tagName = tagName;
    }

    public String getTagCode() {
        return tagCode;
    }

    public void setTagCode(String tagCode) {
        this.tagCode = tagCode;
    }

    public String getCategoryId() {
        return categoryId;
    }

    public void setCategoryId(String categoryId) {
        this.categoryId = categoryId;
    }

    public Long getParentId() {
        return parentId;
    }

    public void setParentId(Long parentId) {
        this.parentId = parentId;
    }

    public Integer getTagLevel() {
        return tagLevel;
    }

    public void setTagLevel(Integer tagLevel) {
        this.tagLevel = tagLevel;
    }

    public Integer getSortOrder() {
        return sortOrder;
    }

    public void setSortOrder(Integer sortOrder) {
        this.sortOrder = sortOrder;
    }
}
