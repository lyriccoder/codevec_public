package JavaExtractor;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.LinkedList;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadPoolExecutor;

import org.kohsuke.args4j.CmdLineException;

import JavaExtractor.Common.CommandLineValues;
import JavaExtractor.FeaturesEntities.ProgramRelation;
import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPubSub;

public class App {
	private static CommandLineValues s_CommandLineValues;
	private static ExtractFeaturesTask extractFeaturesTask;
	private static Jedis jedis = new Jedis("10.198.127.160");

	static class MyListener extends JedisPubSub {
		public void onMessage(String channel, String message) {
			System.out.println("Received: " + message);
			jedis.publish("responses", extractFeaturesTask.process(message));
		}

		public void onSubscribe(String channel, int subscribedChannels) {
		}

		public void onUnsubscribe(String channel, int subscribedChannels) {
		}

		public void onPSubscribe(String pattern, int subscribedChannels) {
		}

		public void onPUnsubscribe(String pattern, int subscribedChannels) {
		}

		public void onPMessage(String pattern, String channel, String message) {
		}
	}

	public static void main(String[] args) {
		setupRedis();
		try {
			s_CommandLineValues = new CommandLineValues(args);
		} catch (CmdLineException e) {
			e.printStackTrace();
			return;
		}
		extractFeaturesTask = new ExtractFeaturesTask(s_CommandLineValues);

	}
	static void setupRedis() {
		MyListener l = new MyListener();
		jedis.subscribe(l, "requests");
	}

}
