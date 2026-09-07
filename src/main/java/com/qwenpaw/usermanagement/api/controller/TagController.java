package com.qwenpaw.usermanagement.api.controller;

import com.qwenpaw.usermanagement.model.dto.TagDTO;
import com.qwenpaw.usermanagement.model.request.CreateTagRequest;
import com.qwenpaw.usermanagement.common.model.PageResult;
import com.qwenpaw.usermanagement.service.TagService;
import org.springframework.web.bind.annotation.*;

/**
 * 标签管理控制器
 */
@RestController
@RequestMapping("/api/v1/tags")
public class TagController {

    private final TagService tagService;

    public TagController(TagService tagService) {
        this.tagService = tagService;
    }

    @PostMapping
    public TagDTO createTag(@RequestBody CreateTagRequest request) {
        return tagService.createTag(request);
    }

    @PutMapping("/{tagId}")
    public TagDTO updateTag(@PathVariable String tagId, @RequestBody CreateTagRequest request) {
        return tagService.updateTag(tagId, request);
    }

    @DeleteMapping("/{tagId}")
    public boolean deleteTag(@PathVariable String tagId) {
        return tagService.deleteTag(tagId);
    }

    @GetMapping("/{tagId}")
    public TagDTO getTagById(@PathVariable String tagId) {
        return tagService.getTagById(tagId);
    }

    @GetMapping
    public PageResult<TagDTO> listTags(
            @RequestParam(required = false) String categoryId,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int pageSize) {
        return tagService.listTags(categoryId, page, pageSize);
    }
}
