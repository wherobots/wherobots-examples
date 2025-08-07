package com.wherobots.sedona

import org.apache.log4j.{Level, Logger}
import org.apache.sedona.spark.SedonaContext
import org.apache.spark.sql.SaveMode
import org.apache.spark.sql.functions.desc
import org.scalatest.BeforeAndAfterAll
import org.scalatest.funspec.AnyFunSpec
import org.scalatest.matchers.should.Matchers

class ScalaTest extends AnyFunSpec with BeforeAndAfterAll with Matchers {
  describe("WherobotsDB Tests") {
    it("should read shapefiles from S3 and write to GeoParquet") {
      Logger.getRootLogger.setLevel(Level.WARN)
      Logger.getLogger("org.apache").setLevel(Level.WARN)
      Logger.getLogger("com").setLevel(Level.WARN)
      Logger.getLogger("akka").setLevel(Level.WARN)

      val s3BucketName = "wherobots-examples"
      val config = SedonaContext.builder()
        .config(s"spark.hadoop.fs.s3a.bucket.$s3BucketName.aws.credentials.provider","org.apache.hadoop.fs.s3a.AnonymousAWSCredentialsProvider")
        .config("spark.hadoop.fs.s3.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3n.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .master("local[*]")
        .getOrCreate()
      val sedona = SedonaContext.create(config)

      // Read the countries shapefiles from S3 using the DataFrame-based reader
      val countries_df = sedona.read
        .format("shapefile")
        .load(s"s3://$s3BucketName/data/ne_50m_admin_0_countries_lakes/")
      countries_df.createOrReplaceTempView("country")
      countries_df.printSchema()

      // Read the airports shapefiles from S3 using the DataFrame-based reader
      val airports_df = sedona.read
        .format("shapefile")
        .load(s"s3://$s3BucketName/data/ne_50m_airports/")
      airports_df.createOrReplaceTempView("airport")
      airports_df.printSchema()

      // Run a spatial join query to find airports in each country
      val result = sedona.sql("SELECT c.geometry as country_geom, c.NAME_EN, a.geometry as airport_geom, a.name FROM country c, airport a WHERE ST_Contains(c.geometry, a.geometry)")

      // Aggregate the results to find the number of airports in each country
      val aggregateResult = result.groupBy("NAME_EN", "country_geom").count()
      aggregateResult.orderBy(desc("count")).show()

      // Write the results to a GeoParquet file
      aggregateResult.write.format("geoparquet").mode(SaveMode.Overwrite).save("airport_country.parquet")
    }
  }
}
