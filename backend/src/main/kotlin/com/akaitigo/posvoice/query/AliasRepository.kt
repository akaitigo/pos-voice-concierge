package com.akaitigo.posvoice.query

import io.quarkus.hibernate.orm.panache.kotlin.PanacheRepositoryBase
import jakarta.enterprise.context.ApplicationScoped
import java.time.OffsetDateTime
import java.time.ZoneOffset

@ApplicationScoped
class AliasRepository : PanacheRepositoryBase<AliasEntity, String> {

    /**
     * 表記ゆれエイリアスを保存する (UPSERT).
     */
    fun saveAlias(alias: String, productName: String) {
        val existing = findById(alias)
        if (existing != null) {
            existing.productName = productName
            existing.createdAt = OffsetDateTime.now(ZoneOffset.UTC)
            persist(existing)
        } else {
            val entity = AliasEntity()
            entity.alias = alias
            entity.productName = productName
            entity.createdAt = OffsetDateTime.now(ZoneOffset.UTC)
            persist(entity)
        }
    }

    /**
     * 全エイリアスを取得する.
     */
    fun findAllAliases(): List<AliasEntity> {
        return listAll()
    }
}
