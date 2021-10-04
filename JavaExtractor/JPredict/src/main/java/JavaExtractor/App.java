package JavaExtractor;

import jdk.nashorn.internal.objects.NativeJSON;
import netscape.javascript.JSObject;
import org.kohsuke.args4j.CmdLineException;

import JavaExtractor.Common.CommandLineValues;
import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPubSub;

import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import java.util.stream.Collectors;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

public class App {
	private static CommandLineValues s_CommandLineValues;
	private static ExtractFeaturesTask extractFeaturesTask;
	private static Jedis clientForSubscribe = new Jedis("localhost");
	private static Jedis clientToPublish = new Jedis("localhost");

	static class CodeListener extends JedisPubSub {

		public void onMessage(String channel, String message) {
			try {
				ObjectMapper receiveMapper = new ObjectMapper();
				Map<String, String> map = receiveMapper.readValue(message, Map.class);
				System.out.println("Received: " + map.get("uuid"));

				String res = extractFeaturesTask.process(map.get("code"));
				clientToPublish.publish(map.get("uuid"), res);
			}
			catch (Exception e) {
				e.printStackTrace();
			}
		}
	}

	public static void main(String[] args) {
		try {
			s_CommandLineValues = new CommandLineValues(args);
		} catch (CmdLineException e) {
			e.printStackTrace();
			return;
		}
		extractFeaturesTask = new ExtractFeaturesTask(s_CommandLineValues);
		CodeListener l = new CodeListener();
		clientForSubscribe.subscribe(l, "requests");
	}

}
