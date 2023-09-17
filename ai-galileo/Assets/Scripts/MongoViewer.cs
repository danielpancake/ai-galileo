using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using MongoDB.Driver;
using MongoDB.Bson;

public class Model_Story
{
    public ObjectId _id { set; get; }
    public string theme { set; get; }
    public List<Model_StoryNode> pre_story { set; get; }
    public List<Model_StoryNode> story { set; get; }
    public List<Model_StoryNode> post_story { set; get; }
    public string requested_by { set; get; }
}

public class Model_StoryNode
{
    public string type { set; get; }
    public string voice { set; get; }
    public string action { set; get; }
    public string text { set; get; }
}

public class MongoViewer : MonoBehaviour
{
    private const string MONGO_URI = "mongodb://localhost:27017";
    private const string MONGO_DATABASE = "ai-galileo";
    private MongoClient client;
    private IMongoDatabase db;

    void Start()
    {
        client = new MongoClient(MONGO_URI);
        db = client.GetDatabase(MONGO_DATABASE);

        // Get all stories
        List<Model_Story> stories = getStories();
        foreach (Model_Story story in stories)
        {
            for (int i = 0; i < story.story.Count; i++)
            {
                Model_StoryNode node = story.story[i];
                Debug.Log(node.type + " " + node.voice + " " + node.action + " " + node.text);
            }
        }
    }

    // Update is called once per frame
    void Update()
    {

    }

    List<Model_Story> getStories()
    {
        // Retrieve all stories
        return db.GetCollection<Model_Story>("stories").Find(_ => true).ToList();
    }
}
