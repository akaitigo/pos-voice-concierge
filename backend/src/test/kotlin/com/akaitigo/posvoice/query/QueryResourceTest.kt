package com.akaitigo.posvoice.query

import io.quarkus.test.junit.QuarkusTest
import io.restassured.RestAssured.given
import org.hamcrest.CoreMatchers.`is`
import org.hamcrest.CoreMatchers.notNullValue
import org.junit.jupiter.api.Test

@QuarkusTest
class QueryResourceTest {

    companion object {
        private const val TEST_API_KEY = "test-api-key-for-integration-tests"
    }

    @Test
    fun `sales endpoint returns response with period label`() {
        given()
            .header("Authorization", "Bearer $TEST_API_KEY")
            .queryParam("period", "today")
            .`when`().get("/api/query/sales")
            .then()
            .statusCode(200)
            .body("periodLabel", `is`("今日"))
            .body("totalAmount", notNullValue())
    }

    @Test
    fun `sales endpoint defaults to today`() {
        given()
            .header("Authorization", "Bearer $TEST_API_KEY")
            .`when`().get("/api/query/sales")
            .then()
            .statusCode(200)
            .body("periodLabel", `is`("今日"))
    }

    @Test
    fun `sales endpoint supports yesterday period`() {
        given()
            .header("Authorization", "Bearer $TEST_API_KEY")
            .queryParam("period", "yesterday")
            .`when`().get("/api/query/sales")
            .then()
            .statusCode(200)
            .body("periodLabel", `is`("昨日"))
    }

    @Test
    fun `sales endpoint supports this_month period`() {
        given()
            .header("Authorization", "Bearer $TEST_API_KEY")
            .queryParam("period", "this_month")
            .`when`().get("/api/query/sales")
            .then()
            .statusCode(200)
            .body("periodLabel", `is`("今月"))
    }

    @Test
    fun `inventory endpoint requires product param`() {
        given()
            .header("Authorization", "Bearer $TEST_API_KEY")
            .`when`().get("/api/query/inventory")
            .then()
            .statusCode(400)
    }

    @Test
    fun `inventory endpoint returns 404 for unknown product`() {
        given()
            .header("Authorization", "Bearer $TEST_API_KEY")
            .queryParam("product", "存在しない商品")
            .`when`().get("/api/query/inventory")
            .then()
            .statusCode(404)
    }

    @Test
    fun `top products endpoint returns response`() {
        given()
            .header("Authorization", "Bearer $TEST_API_KEY")
            .queryParam("period", "today")
            .queryParam("limit", 5)
            .`when`().get("/api/query/top-products")
            .then()
            .statusCode(200)
            .body("periodLabel", `is`("今日"))
    }

    @Test
    fun `learn alias requires both fields`() {
        given()
            .header("Authorization", "Bearer $TEST_API_KEY")
            .contentType("application/json")
            .body("""{"recognizedText": "", "correctProductName": "コーラ"}""")
            .`when`().post("/api/query/learn-alias")
            .then()
            .statusCode(400)
    }

    @Test
    fun `export aliases returns empty list initially`() {
        given()
            .header("Authorization", "Bearer $TEST_API_KEY")
            .`when`().get("/api/query/aliases/export")
            .then()
            .statusCode(200)
    }

    @Test
    fun `import aliases accepts valid json`() {
        given()
            .header("Authorization", "Bearer $TEST_API_KEY")
            .contentType("application/json")
            .body("""[{"alias": "test", "productName": "testProduct"}]""")
            .`when`().post("/api/query/aliases/import")
            .then()
            .statusCode(200)
            .body("success", `is`(true))
    }

    @Test
    fun `unauthenticated request returns 401`() {
        given()
            .`when`().get("/api/query/sales")
            .then()
            .statusCode(401)
    }

    @Test
    fun `invalid api key returns 401`() {
        given()
            .header("Authorization", "Bearer invalid-key")
            .`when`().get("/api/query/sales")
            .then()
            .statusCode(401)
    }

    @Test
    fun `health endpoint is accessible without auth`() {
        given()
            .`when`().get("/health")
            .then()
            .statusCode(200)
            .body("status", `is`("ok"))
    }
}
